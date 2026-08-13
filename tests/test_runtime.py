"""End-to-end runtime tests with a scripted mock model (no Ollama needed)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from smallcoder.agent.runtime import AgentRuntime
from smallcoder.config import Settings
from smallcoder.models.mock import MockModelClient
from smallcoder.observability.logger import TrajectoryLogger, load_run
from tests.conftest import make_git_repo

BUGGY_APP = """\
USERS = {}


def register(email, password):
    USERS[email.strip().lower()] = password


def login(email, password):
    stored = USERS.get(email.strip())
    return stored is not None and stored == password
"""

TEST_FILE = """\
import app


def setup_function():
    app.USERS.clear()


def test_uppercase_email():
    app.register("a@b.com", "pw")
    assert app.login("A@B.COM", "pw")
"""


@pytest.fixture
def buggy_repo(tmp_path: Path) -> Path:
    return make_git_repo(
        tmp_path / "buggy", {"app.py": BUGGY_APP, "tests/test_app.py": TEST_FILE}
    )


def _settings(tmp_path: Path) -> Settings:
    return Settings(model="mock", runs_dir=tmp_path / "runs", max_steps=10, command_timeout=60)


def _runtime(repo: Path, tmp_path: Path, model: MockModelClient) -> AgentRuntime:
    settings = _settings(tmp_path)
    return AgentRuntime(
        repo_root=repo,
        issue="Login fails when the email address contains uppercase characters.",
        model=model,
        settings=settings,
        logger=TrajectoryLogger(settings.runs_dir),
        test_command=f"{sys.executable} -m pytest -q -p no:cacheprovider",
    )


def test_full_solve_flow(buggy_repo: Path, tmp_path: Path):
    model = MockModelClient(
        [
            {
                "thought_summary": "Read the login code first.",
                "action_type": "read_file",
                "arguments": {"path": "app.py"},
            },
            {
                "thought_summary": "Login must lowercase the email like register does.",
                "action_type": "edit_file",
                "arguments": {
                    "path": "app.py",
                    "old_text": "stored = USERS.get(email.strip())",
                    "new_text": "stored = USERS.get(email.strip().lower())",
                },
            },
            {
                "thought_summary": "Fix applied and it should pass tests now.",
                "action_type": "finish",
                "arguments": {"summary": "Lowercased email on login lookup."},
            },
        ]
    )
    result = _runtime(buggy_repo, tmp_path, model).run()

    assert result.success
    assert result.stop_reason == "verified"
    assert result.files_changed == ["app.py"]
    assert "lower()" in result.diff
    assert result.verification is not None and result.verification.passed
    assert result.structured_output_failures == 0


def test_finish_rejected_when_nothing_changed(buggy_repo: Path, tmp_path: Path):
    # Model tries to finish immediately three times without editing anything.
    finish = {"action_type": "finish", "arguments": {"summary": "done"}}
    model = MockModelClient([finish, finish, finish])
    result = _runtime(buggy_repo, tmp_path, model).run()

    assert not result.success
    assert result.stop_reason == "verification_failed"
    # The rejection observation is fed back to the model.
    assert any(
        "finish rejected" in m["content"]
        for call in model.calls[1:]
        for m in call
        if m["role"] == "user"
    )


def test_structured_output_failure_retry_and_abort(buggy_repo: Path, tmp_path: Path):
    # Every reply is garbage: each step burns 2 model calls (initial + reformat),
    # and after 3 failed steps the run aborts.
    model = MockModelClient(["not json"] * 6)
    result = _runtime(buggy_repo, tmp_path, model).run()

    assert not result.success
    assert result.stop_reason == "output_failures"
    assert result.structured_output_failures == 3
    assert result.model_calls == 6


def test_reformat_retry_recovers(buggy_repo: Path, tmp_path: Path):
    model = MockModelClient(
        [
            "I will read the file now.",  # invalid -> triggers reformat retry
            {
                "action_type": "read_file",
                "arguments": {"path": "app.py"},
            },
            {
                "action_type": "edit_file",
                "arguments": {
                    "path": "app.py",
                    "old_text": "stored = USERS.get(email.strip())",
                    "new_text": "stored = USERS.get(email.strip().lower())",
                },
            },
            {"action_type": "finish", "arguments": {"summary": "fixed"}},
        ]
    )
    result = _runtime(buggy_repo, tmp_path, model).run()
    assert result.success
    assert result.structured_output_failures == 0  # retry recovered; not a failure
    # The reformat request contained the parse error.
    assert any("not a valid action" in m["content"] for m in model.calls[1])


def test_runtime_rejects_non_git_dir(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    settings = _settings(tmp_path)
    with pytest.raises(ValueError, match="not a git repository"):
        AgentRuntime(
            repo_root=plain,
            issue="x",
            model=MockModelClient([]),
            settings=settings,
            logger=TrajectoryLogger(settings.runs_dir),
        )


def test_trajectory_is_logged(buggy_repo: Path, tmp_path: Path):
    model = MockModelClient(
        [
            {"action_type": "read_file", "arguments": {"path": "app.py"}},
            {
                "action_type": "edit_file",
                "arguments": {
                    "path": "app.py",
                    "old_text": "stored = USERS.get(email.strip())",
                    "new_text": "stored = USERS.get(email.strip().lower())",
                },
            },
            {"action_type": "finish", "arguments": {"summary": "fixed"}},
        ]
    )
    runtime = _runtime(buggy_repo, tmp_path, model)
    result = runtime.run()

    run = load_run(_settings(tmp_path).runs_dir, result.run_id)
    assert run["meta"]["issue"].startswith("Login fails")
    events = [e["event"] for e in run["events"]]
    assert "model_call" in events
    assert "step" in events
    assert "verification" in events
    assert run["result"]["success"] is True


def test_prompt_contains_issue_and_repo_map(buggy_repo: Path, tmp_path: Path):
    model = MockModelClient([{"action_type": "finish", "arguments": {}}] * 3)
    _runtime(buggy_repo, tmp_path, model).run()
    first_user = next(m for m in model.calls[0] if m["role"] == "user")["content"]
    assert "Login fails" in first_user
    assert "app.py" in first_user
    assert "tests/test_app.py" in first_user


def test_context_budget_enforced(buggy_repo: Path, tmp_path: Path):
    # Tiny context limit: the assembled prompt must be truncated to budget.
    settings = Settings(
        model="mock", runs_dir=tmp_path / "runs", max_steps=3, context_limit=200
    )
    model = MockModelClient(
        [
            {"action_type": "read_file", "arguments": {"path": "app.py"}},
            {"action_type": "read_file", "arguments": {"path": "tests/test_app.py"}},
            {"action_type": "finish", "arguments": {}},
        ]
    )
    runtime = AgentRuntime(
        repo_root=buggy_repo,
        issue="Login fails with uppercase email.",
        model=model,
        settings=settings,
        logger=TrajectoryLogger(settings.runs_dir),
    )
    runtime.run()
    for call in model.calls:
        user = next(m for m in call if m["role"] == "user")["content"]
        assert len(user) <= settings.prompt_char_budget + 100  # small slack for marker text
