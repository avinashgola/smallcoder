"""Read-only git helpers for repository safety and change tracking.

SmallCoder never commits, pushes, or runs destructive git commands. It only
records the initial state and reports what changed relative to it.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

# Tool-generated noise that should never count as an agent change, even in
# repos that lack a .gitignore (e.g. bytecode caches created by running tests).
NOISE_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def _is_noise(path: str) -> bool:
    return any(part.rstrip("/") in NOISE_PARTS for part in path.split("/"))


@dataclass(frozen=True)
class RepoSnapshot:
    head: str | None  # None for a repo with no commits yet
    dirty_paths: frozenset[str]  # paths already modified/untracked before we started


def _git(repo_root: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=30
    )
    return proc.returncode, proc.stdout


def is_git_repo(path: Path) -> bool:
    code, out = _git(path, "rev-parse", "--is-inside-work-tree")
    return code == 0 and out.strip() == "true"


def head_commit(repo_root: Path) -> str | None:
    code, out = _git(repo_root, "rev-parse", "HEAD")
    return out.strip() if code == 0 else None


def status_paths(repo_root: Path) -> frozenset[str]:
    """Paths that are modified, added, deleted, or untracked (porcelain)."""
    code, out = _git(repo_root, "status", "--porcelain")
    if code != 0:
        return frozenset()
    paths = set()
    for line in out.splitlines():
        if len(line) > 3:
            path = line[3:].strip().strip('"')
            # Rename entries look like "old -> new"; keep the new path.
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if not _is_noise(path):
                paths.add(path)
    return frozenset(paths)


def snapshot(repo_root: Path) -> RepoSnapshot:
    return RepoSnapshot(head=head_commit(repo_root), dirty_paths=status_paths(repo_root))


def changed_since(repo_root: Path, baseline: RepoSnapshot) -> list[str]:
    """Paths changed since the baseline snapshot (excludes pre-existing dirt)."""
    return sorted(status_paths(repo_root) - baseline.dirty_paths)


def working_tree_diff(repo_root: Path, max_chars: int = 20000) -> str:
    """`git diff` of tracked files. Untracked new files are listed, not diffed."""
    code, out = _git(repo_root, "diff")
    diff = out if code == 0 else ""
    code, out = _git(repo_root, "ls-files", "--others", "--exclude-standard")
    untracked = (
        [line for line in out.splitlines() if line.strip() and not _is_noise(line)]
        if code == 0
        else []
    )
    if untracked:
        diff += "\n" + "\n".join(f"new file (untracked): {p}" for p in untracked)
    diff = diff.strip()
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n... [diff truncated] ..."
    return diff
