"""Ways of printing a diff for a human to read."""

from .inline import inline_lines, side_by_side, summarize
from .unified import hunk_header, render_hunk, unified_diff, unified_text

__all__ = [
    "hunk_header",
    "inline_lines",
    "render_hunk",
    "side_by_side",
    "summarize",
    "unified_diff",
    "unified_text",
]
