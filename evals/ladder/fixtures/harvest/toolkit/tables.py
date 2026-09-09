"""Fixed width table rendering for the text report."""


def truncate(text, limit):
    text = str(text)
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def widths_for(rows, headers, limit=28):
    widths = [len(str(header)) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    return [min(width, limit) for width in widths]


def render_row(cells, widths, sep="  "):
    parts = [truncate(cell, widths[i]).ljust(widths[i]) for i, cell in enumerate(cells)]
    return sep.join(parts).rstrip()


def render_table(rows, headers, limit=28):
    widths = widths_for(rows, headers, limit=limit)
    lines = [render_row(headers, widths), render_row(["-" * w for w in widths], widths)]
    lines.extend(render_row(row, widths) for row in rows)
    return "\n".join(lines)
