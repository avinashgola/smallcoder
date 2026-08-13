"""edit_file tool: controlled search/replace edits inside the repository.

The edit contract is exact-unique-match replacement: `old_text` must occur
exactly once in the file. This is deliberately stricter and simpler than
unified diffs, which small models frequently malform. Creating a new file is
expressed as an edit with empty `old_text` against a non-existent path.
"""

from __future__ import annotations

from pathlib import Path

from smallcoder.agent.schemas import EditFileArgs
from smallcoder.tools.base import ToolError, ToolResult, resolve_repo_path


def edit_file(repo_root: Path, args: EditFileArgs) -> ToolResult:
    try:
        target = resolve_repo_path(repo_root, args.path)
    except ToolError as exc:
        return ToolResult(ok=False, output="", error=str(exc))

    rel = str(target.relative_to(repo_root.resolve()))

    if args.old_text == "":
        if target.exists():
            return ToolResult(
                ok=False,
                output="",
                error=(
                    f"{args.path} already exists. To modify it, set old_text to the exact "
                    "text you want to replace."
                ),
            )
        if args.new_text == "":
            return ToolResult(ok=False, output="", error="Refusing to create an empty file.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args.new_text, encoding="utf-8")
        return ToolResult(
            ok=True,
            output=f"Created {rel} ({len(args.new_text.splitlines())} lines).",
            files_touched=[rel],
        )

    if not target.exists():
        return ToolResult(ok=False, output="", error=f"File not found: {args.path}")
    if target.is_dir():
        return ToolResult(ok=False, output="", error=f"{args.path} is a directory.")

    text = target.read_text(encoding="utf-8", errors="replace")
    count = text.count(args.old_text)
    if count == 0:
        return ToolResult(
            ok=False,
            output="",
            error=(
                f"old_text not found in {args.path}. It must match the file exactly, "
                "including whitespace and indentation. Re-read the file and retry."
            ),
        )
    if count > 1:
        return ToolResult(
            ok=False,
            output="",
            error=(
                f"old_text occurs {count} times in {args.path}; it must be unique. "
                "Include more surrounding lines to disambiguate."
            ),
        )
    if args.old_text == args.new_text:
        return ToolResult(ok=False, output="", error="old_text and new_text are identical.")

    target.write_text(text.replace(args.old_text, args.new_text, 1), encoding="utf-8")
    return ToolResult(ok=True, output=f"Edited {rel}.", files_touched=[rel])
