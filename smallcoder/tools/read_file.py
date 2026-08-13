"""read_file tool: read a file or a line range, with line numbers."""

from __future__ import annotations

from pathlib import Path

from smallcoder.agent.schemas import ReadFileArgs
from smallcoder.tools.base import ToolError, ToolResult, resolve_repo_path, truncate_output


def read_file(repo_root: Path, args: ReadFileArgs, max_chars: int = 4000) -> ToolResult:
    try:
        target = resolve_repo_path(repo_root, args.path)
    except ToolError as exc:
        return ToolResult(ok=False, output="", error=str(exc))

    if not target.exists():
        return ToolResult(ok=False, output="", error=f"File not found: {args.path}")
    if target.is_dir():
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
        listing = "\n".join(entries[:100])
        return ToolResult(ok=True, output=f"{args.path} is a directory. Contents:\n{listing}")

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ToolResult(ok=False, output="", error=f"Cannot read {args.path}: {exc}")

    lines = text.splitlines()
    total = len(lines)
    start = args.start_line or 1
    end = args.end_line or total
    if args.start_line and args.end_line and args.end_line < args.start_line:
        return ToolResult(ok=False, output="", error="end_line must be >= start_line")
    selected = lines[start - 1 : end]
    if not selected and total > 0:
        return ToolResult(
            ok=False, output="", error=f"Line range {start}-{end} is outside the file (1-{total})."
        )

    numbered = "\n".join(f"{start + i:5d}| {line}" for i, line in enumerate(selected))
    header = f"{args.path} (lines {start}-{min(end, total)} of {total})"
    return ToolResult(ok=True, output=f"{header}\n{truncate_output(numbered, max_chars)}")
