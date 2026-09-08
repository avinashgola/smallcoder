"""Tests for the generic agent-loop control arm.

Everything here runs on the mock model client — no network, no real inference.

These tests exist mostly to prevent the control from being *accidentally rigged*.
A baseline that quietly gets a weaker oracle, a worse prompt, or a different
stopping rule than the treatment would invalidate the whole comparison, so the
fairness properties are asserted rather than assumed.
"""

from __future__ import annotations

import json

import pytest

from evals.generic_loop import (
    _FALSE_CLAUSE,
    CHARS_PER_TOKEN,
    build_repo_map,
    est_tokens,
    generic_system_prompt,
    run_generic_loop,
)
from evals.run_benchmark import prepare_repo
from smallcoder.agent import prompts
from smallcoder.config import load_settings
from smallcoder.models.mock import MockModelClient
from smallcoder.observability.logger import TrajectoryLogger

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "evals/m3_generalization/fixtures/backoff"
ISSUE = "Setting the retry base delay to 0 should mean retry immediately."
BROKEN = "    base_delay = base_delay or DEFAULT_BASE_DELAY"
FIXED = "    if base_delay is None:\n        base_delay = DEFAULT_BASE_DELAY"

ALLOWED = ("pytest", "python")


def act(action_type, **arguments):
    return json.dumps({"thought_summary": "t", "action_type": action_type,
                       "arguments": arguments, "expected_result": "e"})


@pytest.fixture
def env(tmp_path):
    repo = prepare_repo(FIXTURE)
    settings = load_settings(model="mock", loop_detector=False,
                             stall_verification=False, path_feedback=False)
    logger = TrajectoryLogger(tmp_path / "runs")
    return repo, settings, logger


# ------------------------------------------------------- prompt fairness


def test_generic_prompt_deletes_exactly_one_false_sentence():
    original = prompts.system_prompt(ALLOWED)
    generic = generic_system_prompt(ALLOWED)
    assert _FALSE_CLAUSE in original and _FALSE_CLAUSE not in generic
    # nothing else changed: re-inserting the clause restores the original byte for byte
    assert generic.replace(
        "4. Use finish only when the fix is applied and tests pass.",
        "4. Use finish only when the fix is applied and tests pass." + _FALSE_CLAUSE,
    ) == original
    # rule 3 survives, so the control is still told to run the tests itself
    assert "After editing, run the tests to confirm the fix." in generic


def test_turn_one_is_byte_identical_to_smallcoder(env):
    """The control must not be starved of the issue or the repository map."""
    repo, _, _ = env
    repo_map = build_repo_map(repo)
    assert prompts.build_user_message(ISSUE, repo_map, [], None).startswith("# Issue")
    assert "backoff.py" in repo_map


# --------------------------------------------------------- stopping rule


def test_finish_is_accepted_at_face_value_without_verification(env):
    """The control stops when the model says so — even when it is wrong."""
    repo, settings, logger = env
    model = MockModelClient([act("finish", summary="all fixed")])
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert row["stop_reason"] == "finish_accepted"
    assert row["claimed_success"] == 1
    assert row["verified_final"] == 0        # nothing was actually changed
    assert row["overclaim"] == 1
    assert row["success"] is False
    assert row["steps"] == 1                 # it really did stop immediately


def test_a_correct_fix_verifies_even_though_the_model_never_finished(env):
    """silent_success: the control fixed it and simply never noticed."""
    repo, settings, logger = env
    model = MockModelClient([
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
        act("read_file", path="backoff.py"),
    ] + [act("read_file", path="backoff.py")] * 40)
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert row["stop_reason"] == "max_steps"
    assert row["claimed_success"] == 0
    assert row["verified_final"] == 1
    assert row["silent_success"] == 1
    assert row["success"] is True


def test_delivered_success_when_the_claim_is_correct(env):
    repo, settings, logger = env
    model = MockModelClient([
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
        act("finish", summary="fixed the default handling"),
    ])
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert (row["claimed_success"], row["verified_final"]) == (1, 1)
    assert row["delivered_success"] == 1 and row["overclaim"] == 0


# ------------------------------------------------------- oracle fairness


def test_edited_files_are_tracked_so_the_syntax_check_is_not_silently_dropped(env):
    """verify() omits python_syntax entirely when edited_files is empty.

    If the control failed to track edits it would be graded by a *weaker*
    oracle under the same name — an invisible way to flatter it.
    """
    repo, settings, logger = env
    model = MockModelClient([
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
        act("finish", summary="done"),
    ])
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert "python_syntax" in row["verify_check_names"]
    assert row["files_changed"] == ["backoff.py"]


def test_verification_runs_before_teardown(env):
    """A run that edits must report a non-empty files_changed.

    The benchmark harness deletes the temp repo in a finally block and
    changed_since() returns [] for a missing repo, so verifying too late would
    score every control run as unsolved without any error.
    """
    repo, settings, logger = env
    model = MockModelClient([
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
        act("finish", summary="done"),
    ])
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert row["files_changed"], "edit succeeded but nothing was recorded as changed"


def test_editing_the_tests_is_marked_tampered_and_never_counts_as_success(env):
    repo, settings, logger = env
    target = repo / "tests/test_backoff.py"
    model = MockModelClient([
        act("edit_file", path="tests/test_backoff.py",
            old_text=target.read_text()[:40], new_text="# neutered\n"),
        act("finish", summary="done"),
    ])
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert row["tampered"] == 1
    assert row["success"] is False


# ------------------------------------------------------------- context


def test_context_overflow_is_a_hard_stop_not_an_eviction(env):
    """Dropping oldest messages would be context management — the treatment."""
    repo, settings, logger = env
    huge = "x" * (settings.context_limit * 4)
    model = MockModelClient([act("search_code", query=huge)] * 5)
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert row["stop_reason"] == "context_overflow"
    assert row["steps"] < settings.max_steps


def test_token_estimator_is_conservative():
    assert CHARS_PER_TOKEN <= 3.78  # measured chars/token; under-estimating chars/token
    assert est_tokens([{"role": "user", "content": "a" * 350}]) == 100


# --------------------------------------------- no recovery machinery


def test_no_path_feedback_in_the_control(env):
    """Tool-matched to SmallCoder arm A: identical tools, path feedback off."""
    repo, settings, logger = env
    model = MockModelClient([act("read_file", path="src/backoff.py")] * 40)
    row = run_generic_loop(repo, ISSUE, model, settings, logger)
    assert row["file_not_found_errors"] >= 1
    traj = (logger.run_dir / "trajectory.jsonl").read_text()
    assert "Did you mean" not in traj


def test_snapshots_are_written_for_offline_anytime_scoring(env):
    repo, settings, logger = env
    model = MockModelClient([
        act("read_file", path="backoff.py"),
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
        act("finish", summary="done"),
    ])
    run_generic_loop(repo, ISSUE, model, settings, logger)
    snaps = sorted(p.name for p in (logger.run_dir / "snapshots").iterdir())
    assert "step_000" in snaps and "final" in snaps
    assert (logger.run_dir / "snapshots/final/backoff.py").exists()


# ------------------------------------- tier 2: completion machinery only


def test_with_completion_gates_finish_and_can_rescue(env):
    """The decomposition arm regains the verification gate and stall rescue."""
    repo, settings, logger = env
    model = MockModelClient([
        act("finish", summary="premature"),                       # rejected by the gate
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
        act("finish", summary="now really fixed"),
    ])
    row = run_generic_loop(repo, ISSUE, model, settings, logger, with_completion=True)
    assert row["stop_reason"] == "verified"
    assert row["success"] is True
    assert row["overclaim"] == 0, "a gated finish must never be recorded as an overclaim"


def test_with_completion_rescues_a_silent_success(env):
    repo, settings, logger = env
    settings = load_settings(model="mock", loop_detector=False,
                             stall_verification=True, path_feedback=False)
    model = MockModelClient([
        act("edit_file", path="backoff.py", old_text=BROKEN, new_text=FIXED),
    ] + [act("read_file", path="backoff.py")] * 10)
    row = run_generic_loop(repo, ISSUE, model, settings, logger, with_completion=True)
    assert row["stop_reason"] == "verified_stall_rescue"
    assert row["completion_mode"] == "runtime_rescued"
    assert row["success"] is True
