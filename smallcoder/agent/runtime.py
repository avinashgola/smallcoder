"""The agent runtime: the state machine that owns the loop.

The LLM only ever decides the next single action. The runtime owns:
stepping, structured-output retries, tool dispatch, history compression,
finish-time verification, and hard limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from smallcoder.agent import prompts
from smallcoder.agent.schemas import (
    ActionParseError,
    AgentAction,
    EditFileArgs,
    FinishArgs,
    ReadFileArgs,
    RunCommandArgs,
    SearchCodeArgs,
    parse_action,
)
from smallcoder.agent.state import AgentState, StepRecord
from smallcoder.config import Settings
from smallcoder.gitutils import (
    RepoSnapshot,
    changed_since,
    is_git_repo,
    snapshot,
    working_tree_diff,
)
from smallcoder.models.base import ModelClient, ModelClientError
from smallcoder.observability.logger import TrajectoryLogger
from smallcoder.tools.base import ToolResult
from smallcoder.tools.edit_file import edit_file
from smallcoder.tools.read_file import read_file
from smallcoder.tools.run_command import run_command
from smallcoder.tools.search_code import search_code
from smallcoder.verification.verifier import VerificationResult, verify

MAX_CONSECUTIVE_OUTPUT_FAILURES = 3
MAX_FINISH_ATTEMPTS = 3
RECENT_FULL_OBSERVATIONS = 3
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist"}
MAX_REPO_MAP_FILES = 150


class RunResult(BaseModel):
    run_id: str
    success: bool
    stop_reason: str  # "verified" | "max_steps" | "output_failures" | "model_error" | ...
    steps: int
    model_calls: int
    tokens_in: int
    tokens_out: int
    structured_output_failures: int
    files_changed: list[str]
    diff: str
    verification: VerificationResult | None = None
    final_summary: str = ""


@dataclass
class AgentRuntime:
    repo_root: Path
    issue: str
    model: ModelClient
    settings: Settings
    logger: TrajectoryLogger
    test_command: str | None = None
    on_step: object | None = None  # optional callable(step:int, action:AgentAction|None, ok:bool)
    state: AgentState = field(init=False)
    baseline: RepoSnapshot = field(init=False)

    def __post_init__(self) -> None:
        self.repo_root = self.repo_root.resolve()
        if not self.repo_root.is_dir():
            raise ValueError(f"Repository path does not exist: {self.repo_root}")
        if not is_git_repo(self.repo_root):
            raise ValueError(
                f"{self.repo_root} is not a git repository. "
                "SmallCoder requires git for safety and change tracking (run `git init`)."
            )
        self.state = AgentState(issue=self.issue)
        self.baseline = snapshot(self.repo_root)

    # ------------------------------------------------------------- prompting

    def build_repo_map(self) -> str:
        """Flat file listing with sizes. Deliberately simple in Milestone 1."""
        entries: list[str] = []
        for path in sorted(self.repo_root.rglob("*")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                rel = path.relative_to(self.repo_root)
                entries.append(f"{rel} ({path.stat().st_size} bytes)")
            if len(entries) >= MAX_REPO_MAP_FILES:
                entries.append("... (listing truncated)")
                break
        return "\n".join(entries) if entries else "(empty repository)"

    def build_messages(self, repo_map: str, extra_user: str | None = None) -> list[dict[str, str]]:
        """Assemble the per-step message list within the prompt character budget.

        History policy (V1): the last few observations verbatim, older steps as
        one-line summaries, oldest dropped first when over budget. The real
        context engine arrives in Milestone 3.
        """
        history = self.state.history
        lines: list[str] = []
        for record in history[:-RECENT_FULL_OBSERVATIONS] if history else []:
            lines.append(record.summary_line())
        for record in history[-RECENT_FULL_OBSERVATIONS:]:
            obs = record.observation
            if len(obs) > self.settings.max_tool_output_chars:
                obs = obs[: self.settings.max_tool_output_chars] + "\n...[truncated]"
            lines.append(f"{record.summary_line()}\n{obs}")

        last_observation = None
        if lines:
            last_observation = lines.pop()

        user = prompts.build_user_message(self.issue, repo_map, lines, last_observation)
        if extra_user:
            user += "\n\n" + extra_user

        budget = self.settings.prompt_char_budget
        while len(user) > budget and lines:
            lines.pop(0)  # drop oldest history first
            user = prompts.build_user_message(self.issue, repo_map, lines, last_observation)
            if extra_user:
                user += "\n\n" + extra_user
        if len(user) > budget:
            user = user[:budget] + "\n...[context truncated to fit budget]"

        return [
            {"role": "system", "content": prompts.system_prompt(self.settings.allowed_commands)},
            {"role": "user", "content": user},
        ]

    # ---------------------------------------------------------------- model

    def _next_action(self, repo_map: str) -> tuple[AgentAction, object] | None:
        """One model call with a single reformat retry. None = both attempts invalid."""
        messages = self.build_messages(repo_map)
        response = self.model.complete(messages)
        self.state.model_calls += 1
        self.state.tokens_in += response.tokens_in
        self.state.tokens_out += response.tokens_out
        self.logger.event(
            "model_call",
            step=len(self.state.history) + 1,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            latency_ms=response.latency_ms,
            context_chars=sum(len(m["content"]) for m in messages),
        )
        try:
            return parse_action(response.text)
        except ActionParseError as first_error:
            self.logger.event("parse_error", error=str(first_error), raw=response.text[:2000])
            retry_messages = self.build_messages(
                repo_map, extra_user=prompts.REFORMAT_MESSAGE.format(error=first_error)
            )
            retry = self.model.complete(retry_messages)
            self.state.model_calls += 1
            self.state.tokens_in += retry.tokens_in
            self.state.tokens_out += retry.tokens_out
            try:
                return parse_action(retry.text)
            except ActionParseError as second_error:
                self.state.structured_output_failures += 1
                self.logger.event(
                    "structured_output_failure", error=str(second_error), raw=retry.text[:2000]
                )
                return None

    # ---------------------------------------------------------------- tools

    def _dispatch(self, action: AgentAction, typed_args: object) -> ToolResult:
        if isinstance(typed_args, ReadFileArgs):
            return read_file(self.repo_root, typed_args, self.settings.max_tool_output_chars)
        if isinstance(typed_args, SearchCodeArgs):
            return search_code(self.repo_root, typed_args, self.settings.max_tool_output_chars)
        if isinstance(typed_args, EditFileArgs):
            return edit_file(self.repo_root, typed_args)
        if isinstance(typed_args, RunCommandArgs):
            return run_command(self.repo_root, typed_args, self.settings)
        raise AssertionError(f"Unhandled action: {action.action_type}")

    # ----------------------------------------------------------------- run

    def run(self) -> RunResult:
        repo_map = self.build_repo_map()
        self.logger.write_meta(
            {
                "issue": self.issue,
                "repo": str(self.repo_root),
                "model": getattr(self.model, "model", type(self.model).__name__),
                "settings": {
                    "context_limit": self.settings.context_limit,
                    "max_steps": self.settings.max_steps,
                    "structured_format": self.settings.structured_format,
                },
                "baseline_head": self.baseline.head,
                "baseline_dirty_paths": sorted(self.baseline.dirty_paths),
            }
        )
        if self.baseline.dirty_paths:
            self.logger.event(
                "warning",
                message="repository has uncommitted changes; they are excluded from tracking",
            )

        stop_reason = "max_steps"
        final_summary = ""
        verification: VerificationResult | None = None

        for step in range(1, self.settings.max_steps + 1):
            try:
                parsed = self._next_action(repo_map)
            except ModelClientError as exc:
                self.logger.event("model_error", error=str(exc))
                stop_reason = "model_error"
                final_summary = str(exc)
                break

            if parsed is None:
                self.state.consecutive_output_failures += 1
                record = StepRecord(
                    step=step,
                    action=None,
                    observation="Model produced invalid output twice; step skipped.",
                    ok=False,
                    error_type="STRUCTURED_OUTPUT_ERROR",
                )
                self.state.record_step(record)
                self._notify(step, None, False)
                if self.state.consecutive_output_failures >= MAX_CONSECUTIVE_OUTPUT_FAILURES:
                    stop_reason = "output_failures"
                    final_summary = (
                        f"Aborted after {MAX_CONSECUTIVE_OUTPUT_FAILURES} consecutive "
                        "structured-output failures."
                    )
                    break
                continue

            self.state.consecutive_output_failures = 0
            action, typed_args = parsed

            if action.action_type == "finish":
                self.state.finish_attempts += 1
                verification = verify(
                    self.repo_root,
                    self.settings,
                    self.baseline,
                    self.state.files_edited,
                    self.test_command,
                )
                self.logger.event(
                    "verification",
                    step=step,
                    passed=verification.passed,
                    checks=[c.model_dump() for c in verification.checks],
                )
                if verification.passed:
                    assert isinstance(typed_args, FinishArgs)
                    final_summary = typed_args.summary
                    record = StepRecord(step=step, action=action, observation="verified", ok=True)
                    self.state.record_step(record)
                    self._notify(step, action, True)
                    stop_reason = "verified"
                    break
                observation = (
                    "finish rejected: verification failed -> "
                    + verification.failure_summary()
                    + ". Fix the remaining problems before finishing."
                )
                record = StepRecord(
                    step=step, action=action, observation=observation, ok=False,
                    error_type="VERIFICATION_FAILURE",
                )
                self.state.record_step(record)
                self._notify(step, action, False)
                self.logger.event("step", step=step, action=action.model_dump(), ok=False,
                                  observation=observation)
                if self.state.finish_attempts >= MAX_FINISH_ATTEMPTS:
                    stop_reason = "verification_failed"
                    final_summary = verification.failure_summary()
                    break
                continue

            result = self._dispatch(action, typed_args)
            if result.files_touched:
                self.state.note_edit(result.files_touched)
            if len(result.observation) > self.settings.max_tool_output_chars:
                self.logger.save_output(f"step_{step:03d}.txt", result.observation)
            record = StepRecord(
                step=step,
                action=action,
                observation=result.observation,
                ok=result.ok,
                error_type=None if result.ok else "TOOL_ERROR",
            )
            self.state.record_step(record)
            self._notify(step, action, result.ok)
            self.logger.event(
                "step",
                step=step,
                action=action.model_dump(),
                ok=result.ok,
                files_touched=result.files_touched,
                observation=result.observation[:1000],
            )

        needs_final_verify = verification is None or stop_reason not in ("verified", "model_error")
        if needs_final_verify:
            # Always report final verification state, even on failure paths.
            verification = verify(
                self.repo_root, self.settings, self.baseline,
                self.state.files_edited, self.test_command,
            )

        files_changed = changed_since(self.repo_root, self.baseline)
        diff = working_tree_diff(self.repo_root)
        result = RunResult(
            run_id=self.logger.run_id,
            success=stop_reason == "verified",
            stop_reason=stop_reason,
            steps=len(self.state.history),
            model_calls=self.state.model_calls,
            tokens_in=self.state.tokens_in,
            tokens_out=self.state.tokens_out,
            structured_output_failures=self.state.structured_output_failures,
            files_changed=files_changed,
            diff=diff,
            verification=verification,
            final_summary=final_summary,
        )
        self.logger.write_result(result.model_dump())
        return result

    def _notify(self, step: int, action: AgentAction | None, ok: bool) -> None:
        if callable(self.on_step):
            self.on_step(step, action, ok)
