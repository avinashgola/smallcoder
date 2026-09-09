"""CSV rendering, done by hand so nothing has to touch the filesystem."""

COLUMNS = ("stage", "state", "rows_in", "rows_out", "duration", "error")


def escape(value):
    text = "" if value is None else str(value)
    if any(ch in text for ch in ',"\n'):
        return '"%s"' % text.replace('"', '""')
    return text


def to_csv_lines(summary):
    """Header line plus one line per stage."""
    lines = [",".join(COLUMNS)]
    for outcome in summary.recorded():
        data = outcome.to_dict()
        lines.append(",".join(escape(data[column]) for column in COLUMNS))
    return lines


def to_csv(summary):
    return "\n".join(to_csv_lines(summary))
