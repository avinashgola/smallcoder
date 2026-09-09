"""Render a diff in the usual `@@ -a,b +c,d @@` unified format."""

from diffcore.hunks import CONTEXT, group_hunks
from diffcore.ops import DELETE, EQUAL, INSERT, has_changes
from diffcore.sequence import diff_lines

MARKERS = {EQUAL: " ", DELETE: "-", INSERT: "+"}


def hunk_header(hunk):
    """The `@@ ... @@` line describing where one hunk sits in each file."""
    old_lines = [op for op in hunk if op.tag != INSERT]
    new_lines = [op for op in hunk if op.tag != DELETE]
    old_start = old_lines[0].old + 1 if old_lines else 0
    new_start = new_lines[0].new + 1 if new_lines else 0
    return "@@ -%d,%d +%d,%d @@" % (
        old_start,
        len(old_lines),
        new_start,
        len(new_lines),
    )


def render_hunk(hunk):
    """A hunk header followed by its marked-up lines."""
    return [hunk_header(hunk)] + [MARKERS[op.tag] + op.line for op in hunk]


def unified_diff(old, new, context=CONTEXT):
    """Unified diff lines for two sequences; empty when nothing changed."""
    ops = diff_lines(old, new)
    if not has_changes(ops):
        return []
    lines = []
    for hunk in group_hunks(ops, context):
        lines.extend(render_hunk(hunk))
    return lines


def unified_text(old_text, new_text, context=CONTEXT):
    """Diff two strings line by line and return the diff as one string."""
    return "\n".join(
        unified_diff(old_text.splitlines(), new_text.splitlines(), context)
    )
