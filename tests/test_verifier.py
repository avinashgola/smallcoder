from __future__ import annotations

import sys
from pathlib import Path

from smallcoder.config import Settings
from smallcoder.gitutils import snapshot
from smallcoder.verification.verifier import detect_test_command, verify
from tests.conftest import make_git_repo

PASSING_TEST = "def test_ok():\n    assert True\n"
FAILING_TEST = "def test_bad():\n    assert False\n"


def _settings(tmp_path: Path) -> Settings:
    return Settings(model="mock", runs_dir=tmp_path / "runs", command_timeout=60)


def test_verify_fails_without_changes(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n"})
    base = snapshot(repo)
    result = verify(repo, _settings(tmp_path), base, edited_files=[])
    assert not result.passed
    assert any(c.name == "changes_present" and not c.passed for c in result.checks)


def test_verify_passes_with_change_and_green_tests(tmp_path: Path):
    repo = make_git_repo(
        tmp_path / "r", {"a.py": "x = 1\n", "tests/test_a.py": PASSING_TEST}
    )
    base = snapshot(repo)
    (repo / "a.py").write_text("x = 2\n")
    result = verify(
        repo,
        _settings(tmp_path),
        base,
        edited_files=["a.py"],
        test_command=f"{sys.executable} -m pytest -q -p no:cacheprovider",
    )
    assert result.passed


def test_verify_fails_on_red_tests(tmp_path: Path):
    repo = make_git_repo(
        tmp_path / "r", {"a.py": "x = 1\n", "tests/test_a.py": FAILING_TEST}
    )
    base = snapshot(repo)
    (repo / "a.py").write_text("x = 2\n")
    result = verify(
        repo,
        _settings(tmp_path),
        base,
        edited_files=["a.py"],
        test_command=f"{sys.executable} -m pytest -q -p no:cacheprovider",
    )
    assert not result.passed
    failed = [c for c in result.checks if not c.passed]
    assert failed and failed[0].exit_code == 1


def test_verify_catches_syntax_error(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n"})
    base = snapshot(repo)
    (repo / "a.py").write_text("def broken(:\n")
    result = verify(repo, _settings(tmp_path), base, edited_files=["a.py"])
    assert not result.passed
    syntax = next(c for c in result.checks if c.name == "python_syntax")
    assert not syntax.passed
    assert "a.py" in syntax.summary


def test_verify_ignores_preexisting_dirt(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n", "b.py": "y = 1\n"})
    (repo / "b.py").write_text("y = 2\n")  # dirty BEFORE the baseline snapshot
    base = snapshot(repo)
    result = verify(repo, _settings(tmp_path), base, edited_files=[])
    changes = next(c for c in result.checks if c.name == "changes_present")
    assert not changes.passed  # b.py was already dirty; agent changed nothing


def test_detect_test_command(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"tests/test_x.py": PASSING_TEST})
    assert detect_test_command(repo) is not None
    bare = make_git_repo(tmp_path / "bare", {"a.py": "x = 1\n"})
    assert detect_test_command(bare) is None
