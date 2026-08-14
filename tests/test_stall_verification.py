"""Unit tests for Milestone 2B stall-triggered deterministic verification."""

from __future__ import annotations

import sys
from pathlib import Path

from smallcoder.agent.runtime import AgentRuntime
from smallcoder.config import Settings
from smallcoder.models.mock import MockModelClient
from smallcoder.observability.logger import TrajectoryLogger, load_run
from tests.conftest import make_git_repo

BUGGY = "def add(a, b):\n    return a - b\n"
TESTS = "from app import add\n\ndef test_add():\n    assert add(2, 3) == 5\n"
FIX = {
    "action_type": "edit_file",
    "arguments": {"path": "app.py", "old_text": "return a - b", "new_text": "return a + b"},
}
READ = {"action_type": "read_file", "arguments": {"path": "app.py"}}
PYTEST = f"{sys.executable} -m pytest -q -p no:cacheprovider"


def _settings(tmp_path: Path, **overrides) -> Settings:
    base = {
        "model": "mock",
        "runs_dir": tmp_path / "runs",
        "max_steps": 12,
        "command_timeout": 60,
        "stall_verification": True,
        "stall_check_interval": 5,
    }
    base.update(overrides)
    return Settings(**base)


def _run(repo: Path, tmp_path: Path, script: list[dict], **overrides):
    settings = _settings(tmp_path, **overrides)
    model = MockModelClient(script)
    runtime = AgentRuntime(
        repo_root=repo,
        issue="add() returns the wrong value.",
        model=model,
        settings=settings,
        logger=TrajectoryLogger(settings.runs_dir),
        test_command=PYTEST,
    )
    return runtime.run(), model, settings


def _repo(tmp_path: Path) -> Path:
    return make_git_repo(tmp_path / "r", {"app.py": BUGGY, "tests/test_app.py": TESTS})


def test_runtime_rescues_a_model_that_never_finishes(tmp_path: Path):
    # Model fixes the bug, then reads forever without ever calling finish.
    result, _, _ = _run(tmp_path=tmp_path, repo=_repo(tmp_path), script=[FIX] + [READ] * 11)
    assert result.success
    assert result.stop_reason == "verified_stall_rescue"
    assert result.completion_mode == "runtime_rescued"
    assert result.stall_checks >= 1
    assert result.verification is not None and result.verification.passed


def test_model_initiated_finish_is_recorded_separately(tmp_path: Path):
    script = [FIX, {"action_type": "finish", "arguments": {"summary": "fixed"}}]
    result, _, _ = _run(tmp_path=tmp_path, repo=_repo(tmp_path), script=script)
    assert result.success
    assert result.stop_reason == "verified"
    assert result.completion_mode == "model_initiated"


def test_ablation_flag_disables_rescue(tmp_path: Path):
    result, _, _ = _run(
        tmp_path=tmp_path,
        repo=_repo(tmp_path),
        script=[FIX] + [READ] * 11,
        stall_verification=False,
    )
    assert not result.success
    assert result.stop_reason == "max_steps"
    assert result.completion_mode == "none"
    assert result.stall_checks == 0
    # The fix is present and would verify; the run still fails without M2B.
    assert result.verification is not None and result.verification.passed


def test_no_rescue_when_fix_is_wrong(tmp_path: Path):
    bad_fix = {
        "action_type": "edit_file",
        "arguments": {"path": "app.py", "old_text": "return a - b", "new_text": "return a * b"},
    }
    result, _, _ = _run(tmp_path=tmp_path, repo=_repo(tmp_path), script=[bad_fix] + [READ] * 11)
    assert not result.success
    assert result.stop_reason == "max_steps"
    assert result.stall_checks >= 1  # it checked, and correctly refused to finish


def test_no_stall_check_without_repository_changes(tmp_path: Path):
    result, _, _ = _run(tmp_path=tmp_path, repo=_repo(tmp_path), script=[READ] * 12)
    assert result.stall_checks == 0
    assert not result.success


def test_check_interval_is_respected(tmp_path: Path):
    # Interval 100 with max_steps 12 means the interval never elapses...
    result, _, _ = _run(
        tmp_path=tmp_path,
        repo=_repo(tmp_path),
        script=[FIX] + [READ] * 11,
        stall_check_interval=100,
        loop_detector=False,  # remove the loop-based trigger for this test
    )
    assert result.stall_checks == 0
    assert not result.success


def test_loop_detection_triggers_a_stall_check_early(tmp_path: Path):
    # Interval never elapses, but a detected loop is itself a stall signal.
    result, _, _ = _run(
        tmp_path=tmp_path,
        repo=_repo(tmp_path),
        script=[FIX] + [READ] * 11,
        stall_check_interval=100,
        loop_detector=True,
        loop_repeat_threshold=3,
    )
    assert result.stall_checks >= 1
    assert result.completion_mode == "runtime_rescued"


def test_failed_stall_check_is_not_fed_back_to_the_model(tmp_path: Path):
    """M2B must not change model-facing behavior (no prompt/tool-feedback change)."""
    bad_fix = {
        "action_type": "edit_file",
        "arguments": {"path": "app.py", "old_text": "return a - b", "new_text": "return a * b"},
    }
    _, model, _ = _run(tmp_path=tmp_path, repo=_repo(tmp_path), script=[bad_fix] + [READ] * 11)
    prompts = ["\n".join(m["content"] for m in call) for call in model.calls]
    assert not any("stall" in p.lower() for p in prompts)
    assert not any("runtime-initiated verification" in p.lower() for p in prompts)


def test_stall_events_are_logged(tmp_path: Path):
    result, _, settings = _run(tmp_path=tmp_path, repo=_repo(tmp_path), script=[FIX] + [READ] * 11)
    run = load_run(settings.runs_dir, result.run_id)
    kinds = [e["event"] for e in run["events"]]
    assert "stall_verification" in kinds
    assert "stall_rescue" in kinds
    event = next(e for e in run["events"] if e["event"] == "stall_verification")
    assert event["passed"] is True
    # The stall check runs the same pipeline as finish-time verification.
    names = {c["name"] for c in event["checks"]}
    assert "changes_present" in names and "python_syntax" in names
    assert len(event["checks"]) == 3  # + the configured test command
    assert all(c["passed"] for c in event["checks"])


def test_config_env_parsing(monkeypatch):
    from smallcoder.config import load_settings

    monkeypatch.delenv("SMALLCODER_STALL_VERIFICATION", raising=False)
    assert load_settings().stall_verification is True
    monkeypatch.setenv("SMALLCODER_STALL_VERIFICATION", "0")
    assert load_settings().stall_verification is False
    monkeypatch.setenv("SMALLCODER_STALL_CHECK_INTERVAL", "9")
    assert load_settings().stall_check_interval == 9
