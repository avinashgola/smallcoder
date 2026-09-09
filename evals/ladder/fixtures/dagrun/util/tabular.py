"""A tiny fixed width table renderer for run reports."""

from util.text import truncate


def column_widths(rows, headers, limit=32):
    widths = [len(str(header)) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    return [min(width, limit) for width in widths]


def render_row(cells, widths, sep="  "):
    parts = []
    for index, cell in enumerate(cells):
        text = truncate(str(cell), widths[index])
        parts.append(text.ljust(widths[index]))
    return sep.join(parts).rstrip()


def render_table(rows, headers, limit=32):
    """Render `rows` under `headers`; returns a newline joined string."""
    widths = column_widths(rows, headers, limit=limit)
    lines = [render_row(headers, widths)]
    lines.append(render_row(["-" * width for width in widths], widths))
    for row in rows:
        lines.append(render_row(row, widths))
    return "\n".join(lines)
