from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from smallcoder.config import Settings


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@test.local", "-c", "user.name=test", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def make_git_repo(root: Path, files: dict[str, str]) -> Path:
    """Create a committed git repo containing `files` (relative path -> content)."""
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "initial")
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_git_repo(
        tmp_path / "repo",
        {
            "src/auth.py": (
                "def normalize(email):\n"
                "    return email.strip()\n"
                "\n"
                "def validate_email(email):\n"
                "    return '@' in email\n"
            ),
            "README.md": "demo\n",
        },
    )


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        model="test-model",
        runs_dir=tmp_path / "runs",
        command_timeout=20,
        max_tool_output_chars=2000,
        max_steps=10,
    )
