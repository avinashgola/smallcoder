from __future__ import annotations

from pathlib import Path

from smallcoder.gitutils import (
    changed_since,
    is_git_repo,
    snapshot,
    working_tree_diff,
)
from tests.conftest import make_git_repo


def test_is_git_repo(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n"})
    assert is_git_repo(repo)
    plain = tmp_path / "plain"
    plain.mkdir()
    assert not is_git_repo(plain)


def test_snapshot_and_changed_since(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n"})
    base = snapshot(repo)
    assert base.head is not None
    assert changed_since(repo, base) == []

    (repo / "a.py").write_text("x = 2\n")
    (repo / "new.py").write_text("z = 3\n")
    assert changed_since(repo, base) == ["a.py", "new.py"]


def test_changed_since_excludes_preexisting_dirt(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n"})
    (repo / "a.py").write_text("x = 99\n")
    base = snapshot(repo)  # a.py already dirty at baseline
    (repo / "b.py").write_text("fresh\n")
    assert changed_since(repo, base) == ["b.py"]


def test_working_tree_diff_shows_modifications_and_untracked(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"a.py": "x = 1\n"})
    (repo / "a.py").write_text("x = 2\n")
    (repo / "new.py").write_text("z = 3\n")
    diff = working_tree_diff(repo)
    assert "-x = 1" in diff
    assert "+x = 2" in diff
    assert "new file (untracked): new.py" in diff
