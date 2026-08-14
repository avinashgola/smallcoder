"""Report rendering (not involved in statistics)."""


def render_table(rows):
    if not rows:
        return "(no data)"
    width = max(len(str(r[0])) for r in rows)
    return "\n".join(f"{str(name).ljust(width)}  {value}" for name, value in rows)


def render_header(title):
    return f"{title}\n{'=' * len(title)}"
