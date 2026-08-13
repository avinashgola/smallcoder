"""Unit tests for the Milestone 2A loop detector and its runtime integration."""

from __future__ import annotations

from pathlib import Path

from smallcoder.agent.runtime import AgentRuntime
from smallcoder.config import Settings
from smallcoder.models.mock import MockModelClient
from smallcoder.observability.logger import TrajectoryLogger, load_run
from smallcoder.recovery.loop_detector import (
    LoopDetector,
    diff_state_hash,
    normalize_arguments,
)
from tests.conftest import make_git_repo

# ------------------------------------------------------------- unit: detector


def obs(det, sig="ERROR: not found", diff="d0", args=None, files=(), action="read_file"):
    return det.observe(
        action_type=action,
        arguments=args or {"path": "a.py"},
        files_touched=list(files),
        diff_hash=diff,
        result_signature=sig,
    )


def test_exact_repetition_triggers_at_threshold():
    det = LoopDetector(repeat_threshold=3)
    assert obs(det) is None
    assert obs(det) is None
    detection = obs(det)
    assert detection is not None
    assert detection.kind == "exact_repetition"
    assert detection.count == 3


def test_no_trigger_below_threshold_or_when_state_changes():
    det = LoopDetector(repeat_threshold=3)
    assert obs(det, diff="d0") is None
    assert obs(det, diff="d1") is None
    assert obs(det, diff="d2") is None  # diff changed each time: not the same action


def test_argument_normalization_is_whitespace_insensitive():
    assert normalize_arguments({"path": "a.py", "q": "x   y"}) == normalize_arguments(
        {"q": "x y", "path": "a.py"}
    )


def test_different_result_signature_is_different_fingerprint():
    det = LoopDetector(repeat_threshold=3)
    assert obs(det, sig="ERROR: A") is None
    assert obs(det, sig="ERROR: B") is None
    assert obs(det, sig="ERROR: C") is None


def test_no_progress_cycle_detected():
    det = LoopDetector(repeat_threshold=10, no_progress_window=6)
    # Alternate between two fingerprints; repository never changes.
    for i in range(5):
        result = obs(det, args={"path": "a.py"} if i % 2 == 0 else {"path": "b.py"})
        assert result is None
    detection = obs(det, args={"path": "b.py"})
    assert detection is not None
    assert detection.kind == "no_progress_cycle"


def test_no_progress_cycle_requires_stable_diff():
    det = LoopDetector(repeat_threshold=10, no_progress_window=6)
    for i in range(6):
        detection = obs(
            det,
            args={"path": "a.py"} if i % 2 == 0 else {"path": "b.py"},
            diff=f"d{i % 3}",  # repository state keeps changing
        )
    assert detection is None


def test_reset_clears_history():
    det = LoopDetector(repeat_threshold=3)
    obs(det), obs(det)
    det.reset()
    assert obs(det) is None
    assert obs(det) is None


def test_diff_state_hash_stable_and_sensitive():
    assert diff_state_hash("abc") == diff_state_hash("abc")
    assert diff_state_hash("abc") != diff_state_hash("abd")


# -------------------------------------------------- integration: runtime


REPO_FILES = {
    "app.py": "def f():\n    return 1\n",
    "tests/test_app.py": "from app import f\n\ndef test_f():\n    assert f() == 1\n",
}


def _run(repo: Path, tmp_path: Path, model: MockModelClient, **settings_overrides):
    settings = Settings(
        model="mock",
        runs_dir=tmp_path / "runs",
        max_steps=10,
        command_timeout=30,
        **settings_overrides,
    )
    runtime = AgentRuntime(
        repo_root=repo,
        issue="f() returns the wrong value.",
        model=model,
        settings=settings,
        logger=TrajectoryLogger(settings.runs_dir),
    )
    return runtime.run(), model, settings


def _repeat_action(n: int) -> list[dict]:
    return [{"action_type": "read_file", "arguments": {"path": "app.py"}}] * n


def test_runtime_intervenes_on_exact_repetition(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", REPO_FILES)
    result, model, settings = _run(repo, tmp_path, MockModelClient(_repeat_action(10)))
    assert result.loop_detections >= 1
    assert result.loop_interventions >= 1
    # After the intervention, the next prompt contains the reset instruction.
    prompts = ["\n".join(m["content"] for m in call) for call in model.calls]
    assert any("LOOP DETECTED" in p for p in prompts)
    assert any("meaningfully different strategy" in p for p in prompts)


def test_reset_preserves_discoveries(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", REPO_FILES)
    script = [
        {"action_type": "read_file", "arguments": {"path": "tests/test_app.py"}},
        {"action_type": "run_command", "arguments": {"command": "python3 -c 'import missing_mod'"}},
    ] + _repeat_action(8)
    result, model, _ = _run(repo, tmp_path, MockModelClient(script))
    reset_prompts = [
        "\n".join(m["content"] for m in call)
        for call in model.calls
        if "LOOP DETECTED" in "\n".join(m["content"] for m in call)
    ]
    assert reset_prompts
    # Discoveries preserved: the earlier file read and the command error signature.
    assert "tests/test_app.py" in reset_prompts[0]
    assert "Errors seen" in reset_prompts[0]


def test_interventions_are_bounded(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", REPO_FILES)
    settings_overrides = {"loop_max_interventions": 1, "max_steps": 12}
    settings = Settings(
        model="mock", runs_dir=tmp_path / "runs", command_timeout=30, **settings_overrides
    )
    runtime = AgentRuntime(
        repo_root=repo,
        issue="x",
        model=MockModelClient(_repeat_action(12)),
        settings=settings,
        logger=TrajectoryLogger(settings.runs_dir),
    )
    result = runtime.run()
    assert result.loop_interventions == 1  # capped
    assert result.loop_detections > 1  # detections keep being logged past the cap
    assert result.steps == 12  # steps count iterations, not the compacted history


def test_loop_detection_does_not_declare_success(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", REPO_FILES)
    result, _, _ = _run(repo, tmp_path, MockModelClient(_repeat_action(10)))
    assert not result.success
    assert result.stop_reason == "max_steps"


def test_ablation_flag_disables_detection(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", REPO_FILES)
    result, model, _ = _run(
        repo, tmp_path, MockModelClient(_repeat_action(10)), loop_detector=False
    )
    assert result.loop_detections == 0
    assert result.loop_interventions == 0
    prompts = ["\n".join(m["content"] for m in call) for call in model.calls]
    assert not any("LOOP DETECTED" in p for p in prompts)


def test_loop_events_are_logged(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", REPO_FILES)
    result, _, settings = _run(repo, tmp_path, MockModelClient(_repeat_action(10)))
    run = load_run(settings.runs_dir, result.run_id)
    kinds = [e["event"] for e in run["events"]]
    assert "loop_detected" in kinds
    assert "loop_intervention" in kinds
    detected = next(e for e in run["events"] if e["event"] == "loop_detected")
    assert detected["kind"] in ("exact_repetition", "no_progress_cycle")


def test_config_env_parsing(monkeypatch):
    from smallcoder.config import load_settings

    monkeypatch.delenv("SMALLCODER_LOOP_DETECTOR", raising=False)
    assert load_settings().loop_detector is True  # default on
    monkeypatch.setenv("SMALLCODER_LOOP_DETECTOR", "0")
    assert load_settings().loop_detector is False
    monkeypatch.setenv("SMALLCODER_LOOP_REPEAT_THRESHOLD", "5")
    assert load_settings().loop_repeat_threshold == 5
