"""Shared tool infrastructure: results, repo sandboxing, output truncation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class ToolError(Exception):
    """A tool refused to run or failed in a way the model should be told about."""


@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str | None = None
    files_touched: list[str] = field(default_factory=list)

    @property
    def observation(self) -> str:
        """The text fed back to the model as the result of this action."""
        if self.ok:
            return self.output
        return f"ERROR: {self.error or 'tool failed'}"


def resolve_repo_path(repo_root: Path, path: str) -> Path:
    """Resolve a model-supplied path strictly inside the repository.

    Rejects absolute paths, traversal (`..`), symlink escapes, and anything
    under `.git`. This is the single chokepoint for the repo sandbox boundary.
    """
    if not path or not path.strip():
        raise ToolError("Path must not be empty.")
    candidate = Path(path)
    if candidate.is_absolute():
        raise ToolError(f"Absolute paths are not allowed: {path!r}. Use repo-relative paths.")
    root = repo_root.resolve()
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ToolError(f"Path escapes the repository: {path!r}")
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:  # pragma: no cover - guarded above
        raise ToolError(f"Path escapes the repository: {path!r}") from exc
    if rel.parts and rel.parts[0] == ".git":
        raise ToolError("Access to .git is not allowed.")
    return resolved


def truncate_output(text: str, max_chars: int) -> str:
    """Keep head and tail of long output; the middle is usually noise."""
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    omitted = len(text) - len(head) - len(tail)
    return f"{head}\n... [{omitted} characters truncated] ...\n{tail}"
