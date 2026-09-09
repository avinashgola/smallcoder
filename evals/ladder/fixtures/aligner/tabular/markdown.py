"""Render rows as a markdown table."""

from align.rules import CENTER, RIGHT, place

from .columns import column_widths, detect_alignments, normalize_rows
from .table import resolve_alignments


def divider_cell(width, alignment):
    """The `---`, `---:` or `:---:` marker below one column heading."""
    if alignment == CENTER:
        return ":" + "-" * max(width - 2, 1) + ":"
    if alignment == RIGHT:
        return "-" * max(width - 1, 1) + ":"
    return "-" * max(width, 1)


def _row(cells):
    return "| " + " | ".join(cells) + " |"


def markdown_table(headers, rows, alignments=None):
    """Headings, an alignment divider, then one line per row."""
    columns = len(headers)
    head = normalize_rows([headers], columns)
    body = normalize_rows(rows, columns)
    widths = column_widths(head + body)
    alignments = resolve_alignments(headers, body, alignments)
    lines = [
        _row(
            [place(cell, width, CENTER) for cell, width in zip(head[0], widths)]
        ),
        _row(
            [
                divider_cell(width, alignment)
                for width, alignment in zip(widths, alignments)
            ]
        ),
    ]
    for row in body:
        lines.append(
            _row(
                [
                    place(cell, width, alignment)
                    for cell, width, alignment in zip(row, widths, alignments)
                ]
            )
        )
    return lines


def markdown_text(headers, rows, alignments=None):
    """`markdown_table` as one newline-separated string."""
    return "\n".join(markdown_table(headers, rows, alignments))
