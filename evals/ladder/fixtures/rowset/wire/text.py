"""Writing a table out as text."""

from sheets.errors import TableError

from .header import format_header

EMPTY = "~"
ESCAPES = (("\\", "\\\\"), ("\t", "\\t"), ("\n", "\\n"))


def format_cell(value):
    """Render one cell, escaping the characters the format reserves."""
    if value is None:
        return EMPTY
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if not isinstance(value, str):
        raise TableError("cannot write a value of type %s" % (type(value).__name__,))
    text = value
    for raw, escaped in ESCAPES:
        text = text.replace(raw, escaped)
    if text == EMPTY:
        text = "\\" + EMPTY
    return text


def format_row(row_id, row, column_names):
    cells = [str(row_id)] + [format_cell(row.get(name)) for name in column_names]
    return "\t".join(cells)


def dump_table(table):
    """Return the whole table as text, header included."""
    lines = list(format_header(table))
    names = table.column_names()
    for row_id, row in table.items():
        lines.append(format_row(row_id, row, names))
    return "\n".join(lines) + "\n"
