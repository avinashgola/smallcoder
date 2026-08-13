"""search_code tool: literal text search over the repository.

Uses ripgrep when available; otherwise falls back to a pure-Python walk.
Queries are treated as literal (fixed) strings, which is the most reliable
contract for small models.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from smallcoder.agent.schemas import SearchCodeArgs
from smallcoder.tools.base import ToolError, ToolResult, resolve_repo_path, truncate_output

MAX_MATCH_LINES = 50
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist"}


def _rg_search(repo_root: Path, query: str, search_path: Path) -> list[str] | None:
    rg = shutil.which("rg")
    if not rg:
        return None
    try:
        proc = subprocess.run(
            [
                rg,
                "--no-heading",
                "--line-number",
                "--fixed-strings",
                "--ignore-case",
                "--max-count",
                "10",
                query,
                str(search_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=repo_root,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode not in (0, 1):  # 1 = no matches; anything else = rg error
        return None
    lines = []
    for line in proc.stdout.splitlines():
        # Normalize absolute paths back to repo-relative for the model.
        lines.append(line.replace(str(repo_root) + "/", "", 1))
    return lines


def _python_search(repo_root: Path, query: str, search_path: Path) -> list[str]:
    needle = query.lower()
    matches: list[str] = []
    files = [search_path] if search_path.is_file() else None
    if files is None:
        files = sorted(
            p
            for p in search_path.rglob("*")
            if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)
        )
    for file in files:
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        per_file = 0
        for lineno, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                rel = file.relative_to(repo_root)
                matches.append(f"{rel}:{lineno}:{line.strip()[:200]}")
                per_file += 1
                if per_file >= 10 or len(matches) >= MAX_MATCH_LINES:
                    break
        if len(matches) >= MAX_MATCH_LINES:
            break
    return matches


def search_code(repo_root: Path, args: SearchCodeArgs, max_chars: int = 4000) -> ToolResult:
    try:
        search_path = resolve_repo_path(repo_root, args.path) if args.path else repo_root
    except ToolError as exc:
        return ToolResult(ok=False, output="", error=str(exc))
    if not search_path.exists():
        return ToolResult(ok=False, output="", error=f"Path not found: {args.path}")

    matches = _rg_search(repo_root, args.query, search_path)
    if matches is None:
        matches = _python_search(repo_root, args.query, search_path)
    matches = matches[:MAX_MATCH_LINES]

    if not matches:
        return ToolResult(ok=True, output=f"No matches for {args.query!r}.")
    body = "\n".join(matches)
    return ToolResult(
        ok=True,
        output=f"{len(matches)} match(es) for {args.query!r}:\n{truncate_output(body, max_chars)}",
    )
