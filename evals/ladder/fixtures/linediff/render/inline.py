"""Renderings that are easier to skim than unified diff format."""

from diffcore.ops import DELETE, EQUAL, INSERT, counts, has_changes

SYMBOLS = {EQUAL: "  ", DELETE: "- ", INSERT: "+ "}


def inline_lines(ops):
    """Every line from both sides, each prefixed with a change marker."""
    return [SYMBOLS[op.tag] + op.line for op in ops]


def side_by_side(ops, width=20):
    """Two columns: the original on the left, the update on the right."""
    rows = []
    for op in ops:
        left = "" if op.tag == INSERT else op.line
        right = "" if op.tag == DELETE else op.line
        rows.append("%s | %s" % (left[:width].ljust(width), right[:width]))
    return rows


def summarize(ops):
    """One line describing the size of the change."""
    if not has_changes(ops):
        return "no changes"
    added, removed = counts(ops)
    return "%d added, %d removed" % (added, removed)


def changed_line_numbers(ops):
    """The one-based line numbers touched on each side."""
    removed = [op.old + 1 for op in ops if op.tag == DELETE]
    added = [op.new + 1 for op in ops if op.tag == INSERT]
    return removed, added
