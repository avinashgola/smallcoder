"""A generic single-model agent loop — the control arm SmallCoder is measured against.

Every result in this repository so far compares SmallCoder to SmallCoder with a
flag switched off. That answers "does this mechanism help?" but never "does the
runtime help at all?", because even the fully-ablated arm keeps structured JSON
actions, exact-unique edits, a bounded stateless prompt and verification-gated
completion. This module is the missing control: the same model, the same tools,
the same action schema and the same fixtures, wired into the loop a competent
engineer would write without a runtime — the model manages its own context,
decides for itself when it is done, and gets no recovery machinery.

Nothing here is a reimplementation. The prompt, the tools, the parser, the
verifier, the repo preparation and the model client are all imported from the
package under test, so the only thing that varies is the loop.

Deliberate design decisions, each of which could otherwise rig the result:

* The system prompt is derived from SmallCoder's by deleting exactly one
  sentence — "Verification runs automatically." — which is a true statement
  about the runtime and a false one here. Leaving it would tell the control a
  safety net exists that does not. Nothing else changes.
* Turn 1 is byte-identical to SmallCoder's step-1 user message.
* Context overflow is a hard stop, never an eviction. Dropping oldest messages
  is context management, i.e. the very capability under test; handing the job to
  the inference server would import an undocumented policy instead.
* `finish` is accepted at face value and ends the run — no verification gate.
* The working tree is snapshotted after every step so the run can be scored
  *anytime* offline, not only at its terminal state. SmallCoder stops at the
  first passing checkpoint, so scoring this arm solely at step 30 would compare
  an optimal-stopping maximum against a terminal value and manufacture a gap.

See `results/analysis/generic-loop-preregistration.md` for the frozen design.
"""

from __future__ import annotations

import hashlib
import math
import shutil
import time
from pathlib import Path

from smallcoder.agent import prompts
from smallcoder.agent.schemas import (
    ActionParseError,
    AgentAction,
    EditFileArgs,
    ReadFileArgs,
    RunCommandArgs,
    SearchCodeArgs,
    parse_action,
)
from smallcoder.agent.state import AgentState
from smallcoder.gitutils import changed_since, snapshot, working_tree_diff
from smallcoder.models.base import ModelClientError
from smallcoder.observability.logger import TrajectoryLogger
from smallcoder.tools.base import ToolResult
from smallcoder.tools.edit_file import edit_file
from smallcoder.tools.read_file import read_file
from smallcoder.tools.run_command import run_command
from smallcoder.tools.search_code import search_code
from smallcoder.verification.verifier import verify

# Mirrors smallcoder.agent.runtime; kept as an infrastructure guard, not as
# agent intelligence. MAX_FINISH_ATTEMPTS has no analogue: finish is terminal.
MAX_CONSECUTIVE_OUTPUT_FAILURES = 3
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist"}
MAX_REPO_MAP_FILES = 150

# Conservative against the ~3.78 chars/token measured over 5,668 recorded calls
# (p10 3.54) and against the 4.0 assumed by Settings.prompt_char_budget. Frozen.
CHARS_PER_TOKEN = 3.5
CONTEXT_HEADROOM_TOKENS = 512

_FALSE_CLAUSE = " Verification runs automatically."


def generic_system_prompt(allowed_commands: tuple[str, ...]) -> str:
    """SmallCoder's system prompt minus the one sentence that is false here.

    Rule 4's first clause ("Use finish only when the fix is applied and tests
    pass") is true in both arms and stays. Rule 3 already tells the model to run
    the tests itself, so no instruction is added to compensate — adding one
    would give the control guidance the treatment never receives.
    """
    if prompts.SYSTEM_PROMPT.count(_FALSE_CLAUSE) != 1:
        raise AssertionError("SYSTEM_PROMPT changed; re-derive the generic prompt deliberately")
    generic = prompts.SYSTEM_PROMPT.replace(_FALSE_CLAUSE, "")
    return generic.replace("{allowed_commands}", ", ".join(allowed_commands))


def prompt_digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def build_repo_map(repo_root: Path) -> str:
    """Copied verbatim from AgentRuntime.build_repo_map so turn 1 matches."""
    entries: list[str] = []
    for path in sorted(repo_root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            rel = path.relative_to(repo_root)
            entries.append(f"{rel} ({path.stat().st_size} bytes)")
        if len(entries) >= MAX_REPO_MAP_FILES:
            entries.append("... (listing truncated)")
            break
    return "\n".join(entries) if entries else "(empty repository)"


def est_tokens(messages: list[dict[str, str]]) -> int:
    return math.ceil(sum(len(m["content"]) for m in messages) / CHARS_PER_TOKEN)


def _dispatch(repo_root: Path, typed_args: object, settings) -> ToolResult:
    """Identical tool implementations, with path feedback off (tool-matched)."""
    if isinstance(typed_args, ReadFileArgs):
        return read_file(repo_root, typed_args, settings.max_tool_output_chars,
                         path_feedback=False)
    if isinstance(typed_args, SearchCodeArgs):
        return search_code(repo_root, typed_args, settings.max_tool_output_chars)
    if isinstance(typed_args, EditFileArgs):
        return edit_file(repo_root, typed_args, path_feedback=False)
    if isinstance(typed_args, RunCommandArgs):
        return run_command(repo_root, typed_args, settings)
    raise AssertionError(f"Unhandled action type: {typed_args!r}")


def _snapshot_tree(repo_root: Path, snap_dir: Path, label: str) -> None:
    """Copy the working tree (including .git) so the run can be scored offline."""
    dest = snap_dir / label
    if dest.exists():
        return
    shutil.copytree(repo_root, dest, symlinks=True)


def run_generic_loop(
    repo_root: Path,
    issue: str,
    model,
    settings,
    logger: TrajectoryLogger,
    with_completion: bool = False,
) -> dict:
    """Run one generic-loop episode and score it post-hoc.

    ``with_completion`` is the Tier-2 decomposition arm: identical in every way
    except that it regains SmallCoder's completion machinery (a verification
    gate on ``finish`` plus stall-triggered verification). It isolates the
    completion pathway from context policy and recovery, which the frozen data
    suggest is where nearly all of SmallCoder's advantage lives.
    """
    baseline = snapshot(repo_root)
    repo_map = build_repo_map(repo_root)
    system = generic_system_prompt(settings.allowed_commands)
    snap_dir = logger.run_dir / "snapshots"
    snap_dir.mkdir(exist_ok=True)

    logger.write_meta({
        "issue": issue,
        "repo": str(repo_root),
        "model": getattr(model, "model", type(model).__name__),
        "arm": "generic+completion" if with_completion else "generic",
        "settings": {
            "context_limit": settings.context_limit,
            "max_steps": settings.max_steps,
            "structured_format": settings.structured_format,
            "chars_per_token": CHARS_PER_TOKEN,
            "context_headroom_tokens": CONTEXT_HEADROOM_TOKENS,
            "with_completion": with_completion,
        },
        "prompt_sha256": prompt_digest(system),
        "baseline_head": baseline.head,
    })

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompts.build_user_message(issue, repo_map, [], None)},
    ]
    state = AgentState(issue=issue)
    stop_reason = "max_steps"
    claimed_success = 0
    first_finish_step = -1
    consecutive_output_failures = 0
    commands_run = edits_ok = edits_failed = 0
    peak_context_chars = chars_sent_total = 0
    model_latency_ms_total = 0.0
    steps_taken = 0
    stall_passed = False

    # Stall-verification bookkeeping (Tier 2 only; mirrors AgentRuntime).
    last_check_step = 0
    last_diff_hash: str | None = None

    _snapshot_tree(repo_root, snap_dir, "step_000")

    for step in range(1, settings.max_steps + 1):
        steps_taken = step
        chars = sum(len(m["content"]) for m in messages)
        peak_context_chars = max(peak_context_chars, chars)
        if est_tokens(messages) > settings.context_limit - CONTEXT_HEADROOM_TOKENS:
            logger.event("context_overflow", step=step, chars=chars,
                         est_tokens=est_tokens(messages), n_messages=len(messages))
            stop_reason = "context_overflow"
            break

        action: AgentAction | None = None
        typed_args: object = None
        for attempt in (1, 2):
            started = time.monotonic()
            try:
                response = model.complete(messages)
            except ModelClientError as exc:
                logger.event("model_error", error=str(exc))
                stop_reason = "model_error"
                return _finalize(
                    repo_root, baseline, settings, state, logger, snap_dir, stop_reason,
                    steps_taken, claimed_success, first_finish_step, commands_run,
                    edits_ok, edits_failed, peak_context_chars, chars_sent_total,
                    model_latency_ms_total, messages, error=str(exc)[:200],
                )
            model_latency_ms_total += (time.monotonic() - started) * 1000
            chars_sent_total += chars
            state.model_calls += 1
            state.tokens_in += response.tokens_in
            state.tokens_out += response.tokens_out
            # The assistant turn is kept verbatim and forever — including a
            # malformed one. Discarding it would be a silent repair mechanism.
            messages.append({"role": "assistant", "content": response.text})
            logger.event("model_call", step=step, attempt=attempt,
                         tokens_in=response.tokens_in, tokens_out=response.tokens_out,
                         context_chars=chars, n_messages=len(messages))
            try:
                action, typed_args = parse_action(response.text)
                break
            except ActionParseError as exc:
                logger.event("parse_error", step=step, attempt=attempt, error=str(exc))
                if attempt == 1:
                    messages.append({
                        "role": "user",
                        "content": prompts.REFORMAT_MESSAGE.format(error=str(exc)),
                    })
                    chars = sum(len(m["content"]) for m in messages)

        if action is None:
            state.structured_output_failures += 1
            consecutive_output_failures += 1
            messages.append({
                "role": "user",
                "content": "Model produced invalid output twice; step skipped.",
            })
            if consecutive_output_failures >= MAX_CONSECUTIVE_OUTPUT_FAILURES:
                stop_reason = "output_failures"
                break
            continue
        consecutive_output_failures = 0

        if action.action_type == "finish":
            claimed_success = 1
            first_finish_step = step
            if not with_completion:
                stop_reason = "finish_accepted"  # face value: no verification gate
                break
            gate = verify(repo_root, settings, baseline, state.files_edited, None)
            logger.event("verification", step=step, passed=gate.passed,
                         checks=[c.model_dump() for c in gate.checks])
            if gate.passed:
                stop_reason = "verified"
                break
            messages.append({"role": "user", "content": gate.failure_summary()})
            continue

        result = _dispatch(repo_root, typed_args, settings)
        if action.action_type == "run_command":
            commands_run += 1
        if action.action_type == "edit_file":
            edits_ok += 1 if result.ok else 0
            edits_failed += 0 if result.ok else 1
        if result.files_touched:
            state.note_edit(result.files_touched)
        if result.file_not_found:
            state.file_not_found_errors += 1

        obs = result.observation
        if len(obs) > settings.max_tool_output_chars:
            logger.save_output(f"step_{step:03d}.txt", obs)
            obs = obs[: settings.max_tool_output_chars] + "\n...[truncated]"
        # Raw. No "Step N: <action> -> ok" label, no section headers, no
        # imperative closer: those are runtime scaffolding, not the control's.
        messages.append({"role": "user", "content": obs})
        logger.event("step", step=step,
                     action={"action_type": action.action_type, "arguments": action.arguments},
                     ok=result.ok, error=result.error)
        _snapshot_tree(repo_root, snap_dir, f"step_{step:03d}")

        if with_completion and not stall_passed:
            passed, last_check_step, last_diff_hash = _maybe_stall_verify(
                repo_root, baseline, settings, state, logger, step,
                last_check_step, last_diff_hash,
            )
            if passed:
                stop_reason = "verified_stall_rescue"
                stall_passed = True
                break

    return _finalize(
        repo_root, baseline, settings, state, logger, snap_dir, stop_reason,
        steps_taken, claimed_success, first_finish_step, commands_run,
        edits_ok, edits_failed, peak_context_chars, chars_sent_total,
        model_latency_ms_total, messages,
    )


def _maybe_stall_verify(repo_root, baseline, settings, state, logger, step,
                        last_check_step, last_diff_hash):
    """Tier-2 only. Byte-for-byte the gating in AgentRuntime._maybe_stall_verify."""
    from smallcoder.recovery.loop_detector import diff_state_hash

    if not changed_since(repo_root, baseline):
        return False, last_check_step, last_diff_hash
    if (step - last_check_step) < settings.stall_check_interval:
        return False, last_check_step, last_diff_hash
    diff_hash = diff_state_hash(working_tree_diff(repo_root))
    if diff_hash == last_diff_hash:
        return False, last_check_step, last_diff_hash
    state.stall_checks += 1
    result = verify(repo_root, settings, baseline, state.files_edited, None)
    logger.event("stall_verification", step=step, passed=result.passed,
                 checks=[c.model_dump() for c in result.checks])
    return result.passed, step, diff_hash


def _finalize(repo_root, baseline, settings, state, logger, snap_dir, stop_reason,
              steps_taken, claimed_success, first_finish_step, commands_run,
              edits_ok, edits_failed, peak_context_chars, chars_sent_total,
              model_latency_ms_total, messages, error: str | None = None) -> dict:
    """Score the run at its own stopping point, before the repo is torn down.

    Verification MUST happen here rather than in the caller: the benchmark
    harness removes the temp repo in a ``finally`` block, and ``changed_since``
    returns an empty list for a missing repo, so a late call would silently
    score every run as unsolved.
    """
    _snapshot_tree(repo_root, snap_dir, "final")
    verification = verify(repo_root, settings, baseline, state.files_edited, None)
    files_changed = changed_since(repo_root, baseline)
    verified_final = 1 if verification.passed else 0
    tampered = 1 if any(
        f.startswith("tests/") or Path(f).name in ("conftest.py",) or "test_" in Path(f).name
        for f in files_changed
    ) else 0

    row = {
        "success": bool(verified_final and not tampered),
        "stop_reason": stop_reason,
        "steps": steps_taken,
        "model_calls": state.model_calls,
        "tokens_in": state.tokens_in,
        "tokens_out": state.tokens_out,
        "structured_output_failures": state.structured_output_failures,
        "file_not_found_errors": state.file_not_found_errors,
        "stall_checks": state.stall_checks,
        # New endpoints. verified_final is the primary; the anytime numbers are
        # filled in offline by evals/replay_verify.py from the snapshots.
        "claimed_success": claimed_success,
        "verified_final": verified_final,
        "overclaim": 1 if (claimed_success and not verified_final) else 0,
        "silent_success": 1 if (not claimed_success and verified_final) else 0,
        "delivered_success": 1 if (claimed_success and verified_final) else 0,
        "first_finish_step": first_finish_step,
        "tampered": tampered,
        "commands_run": commands_run,
        "edits_ok": edits_ok,
        "edits_failed": edits_failed,
        "peak_context_chars": peak_context_chars,
        "chars_sent_total": chars_sent_total,
        "n_messages_final": len(messages),
        "model_latency_ms_total": round(model_latency_ms_total, 1),
        "completion_mode": (
            "model_initiated" if stop_reason in ("finish_accepted", "verified")
            else "runtime_rescued" if stop_reason == "verified_stall_rescue"
            else "none"
        ),
        "final_verification_passed": verification.passed,
        "files_changed": files_changed,
        "verify_check_names": [c.name for c in verification.checks],
        "run_id": logger.run_id,
    }
    if error:
        row["error"] = error
    logger.write_result(row)
    return row


def run_one_generic(task: dict, model_name: str, with_completion: bool = False) -> dict:
    """Benchmark entry point for one control run — mirrors run_benchmark.run_one.

    Imports prepare_repo and the client construction rather than duplicating
    them, so the only difference from the treatment arm is the loop itself.
    """
    import shutil as _shutil

    from evals.run_benchmark import ROOT as BENCH_ROOT
    from evals.run_benchmark import prepare_repo
    from smallcoder.config import load_settings
    from smallcoder.models.ollama import OllamaClient

    settings = load_settings(
        model=model_name,
        loop_detector=False,
        stall_verification=with_completion,
        path_feedback=False,
    )
    client = OllamaClient(
        base_url=settings.base_url,
        model=settings.model,
        request_timeout=settings.request_timeout,
        structured_format=settings.structured_format,
        num_ctx=settings.context_limit,
        force_ipv4=settings.force_ipv4,
    )
    repo = prepare_repo(BENCH_ROOT / task["fixture"])
    logger = TrajectoryLogger(settings.runs_dir)
    started = time.monotonic()
    try:
        row = run_generic_loop(
            repo_root=repo,
            issue=task["issue"],
            model=client,
            settings=settings,
            logger=logger,
            with_completion=with_completion,
        )
    except ModelClientError as exc:
        row = {"run_id": logger.run_id, "success": False, "stop_reason": "model_error",
               "error": str(exc)[:200]}
    finally:
        client.close()
        _shutil.rmtree(repo.parent, ignore_errors=True)
    row["duration_s"] = round(time.monotonic() - started, 1)
    return row
