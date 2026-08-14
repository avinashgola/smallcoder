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
from smallcoder.recovery.loop_detector import LoopDetector, diff_state_hash
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
    # "verified" | "verified_stall_rescue" | "max_steps" | "output_failures" | "model_error" | ...
    stop_reason: str
    # "model_initiated" (model called finish) | "runtime_rescued" (M2B) | "none"
    completion_mode: str = "none"
    stall_checks: int = 0
    file_not_found_errors: int = 0
    path_suggestions_emitted: int = 0
    path_suggestions_followed: int = 0
    steps: int
    model_calls: int
    tokens_in: int
    tokens_out: int
    structured_output_failures: int
    loop_detections: int = 0
    loop_interventions: int = 0
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
        self._loop_detector = (
            LoopDetector(
                repeat_threshold=self.settings.loop_repeat_threshold,
                no_progress_window=self.settings.loop_no_progress_window,
            )
            if self.settings.loop_detector
            else None
        )
        self._pending_suggestions: list[str] = []  # M3: suggestions awaiting a retry
        # M2B stall-verification bookkeeping
        self._last_stall_check_step = 0
        self._last_stall_diff_hash: str | None = None
        self._loop_since_last_check = False

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

    # ---------------------------------------------------------- loop guard

    def _loop_reset_text(self, detail: str) -> str:
        """Build the strategy-reset observation, preserving useful discoveries."""
        lines = [
            f"LOOP DETECTED: {detail}.",
            "That approach is not working. Do NOT repeat it.",
            "Progress so far (preserved):",
            f"- Files read: {', '.join(self.state.files_read) or '(none)'}",
            f"- Files edited: {', '.join(self.state.files_edited) or '(none)'}"
            + (
                " (a git diff exists with your changes)"
                if self.state.files_edited
                else ""
            ),
        ]
        if self.state.error_signatures:
            lines.append("- Errors seen: " + " | ".join(self.state.error_signatures))
        lines.append(
            "Choose a meaningfully different strategy now: use a different action type, "
            "different arguments, or investigate something you have not looked at yet."
        )
        return "\n".join(lines)

    def _check_for_loop(self, step: int, action: AgentAction, result: ToolResult) -> None:
        if self._loop_detector is None:
            return
        signature = result.observation.splitlines()[0] if result.observation else ""
        detection = self._loop_detector.observe(
            action_type=action.action_type,
            arguments=action.arguments,
            files_touched=result.files_touched,
            diff_hash=diff_state_hash(working_tree_diff(self.repo_root)),
            result_signature=signature,
        )
        if detection is None:
            return
        self.state.loop_detections += 1
        self._loop_since_last_check = True  # M2B: a loop is also a stall signal
        self.logger.event(
            "loop_detected", step=step, kind=detection.kind, detail=detection.detail
        )
        if self.state.loop_interventions >= self.settings.loop_max_interventions:
            return  # bounded: keep logging detections but stop resetting strategy
        self.state.loop_interventions += 1
        reset_record = StepRecord(
            step=step,
            action=None,
            observation=self._loop_reset_text(detection.detail),
            ok=True,
            error_type="LOOP_RESET",
        )
        self.state.history = [reset_record]
        self._loop_detector.reset()
        self.logger.event(
            "loop_intervention", step=step, interventions=self.state.loop_interventions
        )

    # ------------------------------------------------- M2B: stall verification

    def _maybe_stall_verify(self, step: int) -> VerificationResult | None:
        """Run verification when the model has changed code but has not finished.

        Milestone 2A showed that a large share of failed runs already contained a
        complete, verification-passing fix: the model simply never requested
        `finish`. This check runs the same deterministic pipeline the runtime
        would run at `finish` time and returns a passing result when the run can
        be completed by the runtime instead of the model.

        Bounded and side-effect free with respect to the model: it is gated by a
        step interval, skipped unless the working tree changed since the last
        check, and a *failing* result is logged but never fed back into the
        prompt (M2B must not change model-facing behavior).
        """
        if not self.settings.stall_verification:
            return None
        if not changed_since(self.repo_root, self.baseline):
            return None  # nothing has been modified; nothing to verify

        due = (step - self._last_stall_check_step) >= self.settings.stall_check_interval
        if not (due or self._loop_since_last_check):
            return None

        diff_hash = diff_state_hash(working_tree_diff(self.repo_root))
        if diff_hash == self._last_stall_diff_hash:
            return None  # unchanged since the last check: the result would repeat

        self._last_stall_check_step = step
        self._last_stall_diff_hash = diff_hash
        self._loop_since_last_check = False
        self.state.stall_checks += 1

        verification = verify(
            self.repo_root,
            self.settings,
            self.baseline,
            self.state.files_edited,
            self.test_command,
        )
        self.logger.event(
            "stall_verification",
            step=step,
            passed=verification.passed,
            checks=[c.model_dump() for c in verification.checks],
        )
        return verification if verification.passed else None

    def _dispatch(self, action: AgentAction, typed_args: object) -> ToolResult:
        if isinstance(typed_args, ReadFileArgs):
            return read_file(
                self.repo_root,
                typed_args,
                self.settings.max_tool_output_chars,
                path_feedback=self.settings.path_feedback,
            )
        if isinstance(typed_args, SearchCodeArgs):
            return search_code(self.repo_root, typed_args, self.settings.max_tool_output_chars)
        if isinstance(typed_args, EditFileArgs):
            return edit_file(
                self.repo_root, typed_args, path_feedback=self.settings.path_feedback
            )
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
                    "loop_detector": self.settings.loop_detector,
                    "loop_repeat_threshold": self.settings.loop_repeat_threshold,
                    "loop_no_progress_window": self.settings.loop_no_progress_window,
                    "loop_max_interventions": self.settings.loop_max_interventions,
                    "stall_verification": self.settings.stall_verification,
                    "stall_check_interval": self.settings.stall_check_interval,
                    "path_feedback": self.settings.path_feedback,
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
        completion_mode = "none"
        final_summary = ""
        verification: VerificationResult | None = None

        steps_taken = 0
        for step in range(1, self.settings.max_steps + 1):
            steps_taken = step
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
                    completion_mode = "model_initiated"
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
                self.state.note_error(observation)
                self._notify(step, action, False)
                self.logger.event("step", step=step, action=action.model_dump(), ok=False,
                                  observation=observation)
                self._check_for_loop(
                    step, action, ToolResult(ok=False, output=observation, error=observation)
                )
                if self.state.finish_attempts >= MAX_FINISH_ATTEMPTS:
                    stop_reason = "verification_failed"
                    final_summary = verification.failure_summary()
                    break
                continue

            result = self._dispatch(action, typed_args)

            # M3 instrumentation. A suggestion counts as "followed" when the very
            # next file-targeting action uses one of the exact paths we offered,
            # which is unambiguous attribution.
            if self._pending_suggestions and action.action_type in ("read_file", "edit_file"):
                if str(action.arguments.get("path", "")) in self._pending_suggestions:
                    self.state.path_suggestions_followed += 1
                    self.logger.event("path_suggestion_followed", step=step,
                                      path=action.arguments.get("path"))
                self._pending_suggestions = []
            if result.file_not_found:
                self.state.file_not_found_errors += 1
                if result.path_suggestions:
                    self.state.path_suggestions_emitted += 1
                    self._pending_suggestions = list(result.path_suggestions)
                    self.logger.event("path_suggestion", step=step,
                                      requested=action.arguments.get("path"),
                                      suggestions=result.path_suggestions)

            if result.files_touched:
                self.state.note_edit(result.files_touched)
            if action.action_type == "read_file" and result.ok:
                self.state.note_read(str(action.arguments.get("path", "")))
            if not result.ok:
                self.state.note_error(result.observation.splitlines()[0])
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
            self._check_for_loop(step, action, result)

            rescued = self._maybe_stall_verify(step)
            if rescued is not None:
                verification = rescued
                stop_reason = "verified_stall_rescue"
                completion_mode = "runtime_rescued"
                final_summary = (
                    "Runtime-initiated verification passed while the model was still "
                    "working; the fix in the working tree is complete."
                )
                self.logger.event("stall_rescue", step=step)
                break

        verified_reasons = ("verified", "verified_stall_rescue")
        needs_final_verify = verification is None or stop_reason not in (
            *verified_reasons,
            "model_error",
        )
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
            success=stop_reason in verified_reasons,
            stop_reason=stop_reason,
            completion_mode=completion_mode,
            stall_checks=self.state.stall_checks,
            file_not_found_errors=self.state.file_not_found_errors,
            path_suggestions_emitted=self.state.path_suggestions_emitted,
            path_suggestions_followed=self.state.path_suggestions_followed,
            steps=steps_taken,  # len(history) undercounts after loop-reset compaction
            model_calls=self.state.model_calls,
            tokens_in=self.state.tokens_in,
            tokens_out=self.state.tokens_out,
            structured_output_failures=self.state.structured_output_failures,
            loop_detections=self.state.loop_detections,
            loop_interventions=self.state.loop_interventions,
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
