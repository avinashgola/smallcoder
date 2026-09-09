"""Render rows of values as a bordered text table."""

from align.borders import PADDING, join_cells, rule
from align.cells import clip
from align.rules import CENTER, LEFT, place

from .columns import column_widths, detect_alignments, fit_widths, normalize_rows


def render_row(cells, widths, alignments, padding=PADDING):
    """One table row: every cell clipped, placed, then joined."""
    placed = [
        place(clip(cell, width), width, alignment)
        for cell, width, alignment in zip(cells, widths, alignments)
    ]
    return join_cells(placed, padding)


def resolve_alignments(headers, rows, alignments=None):
    """Use the caller's alignments, or work them out from the body rows."""
    if alignments is not None:
        return list(alignments)
    return detect_alignments(rows) or [LEFT] * len(headers)


def render_table(headers, rows, alignments=None, maximum=None, total=None,
                 padding=PADDING):
    """A bordered table with a centred header row above the body."""
    columns = len(headers)
    head = normalize_rows([headers], columns)
    body = normalize_rows(rows, columns)
    widths = column_widths(head + body, maximum=maximum)
    if total is not None:
        widths = fit_widths(widths, total)
    alignments = resolve_alignments(headers, body, alignments)
    separator = rule(widths, padding)
    lines = [separator, render_row(head[0], widths, [CENTER] * columns, padding)]
    lines.append(separator)
    for row in body:
        lines.append(render_row(row, widths, alignments, padding))
    lines.append(separator)
    return lines


def render_text(headers, rows, **options):
    """`render_table` as one newline-separated string."""
    return "\n".join(render_table(headers, rows, **options))
