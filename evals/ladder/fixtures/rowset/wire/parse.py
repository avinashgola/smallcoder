"""Reading a table back from text."""

from sheets.errors import TableError
from sheets.table import Table

from .header import parse_header
from .text import EMPTY

UNESCAPES = (("\\t", "\t"), ("\\n", "\n"))


def parse_cell(text, kind):
    """Turn one written cell back into a value of ``kind``."""
    if text == EMPTY:
        return None
    body = text
    if body == "\\" + EMPTY:
        return EMPTY
    for escaped, raw in UNESCAPES:
        body = body.replace(escaped, raw)
    body = body.replace("\\\\", "\\")
    if kind == "text":
        return body
    if kind == "int":
        return int(body)
    if kind == "float":
        return float(body)
    if kind == "bool":
        return body == "true"
    raise TableError("unknown column type %r" % (kind,))


def load_table(text):
    """Rebuild a table from the output of :func:`~wire.text.dump_table`."""
    lines = [line for line in text.split("\n") if line != ""]
    if len(lines) < 2:
        raise TableError("a dump needs both header lines")
    name, columns = parse_header(lines[:2])
    table = Table(name, columns)
    kinds = [column.kind for column in columns]
    names = [column.name for column in columns]
    for line in lines[2:]:
        if line.startswith("#"):
            continue
        cells = line.split("\t")
        if len(cells) != len(names) + 1:
            raise TableError("row %r has the wrong number of cells" % (line,))
        values = {}
        for name, kind, cell in zip(names, kinds, cells[1:]):
            values[name] = parse_cell(cell, kind)
        table.restore_row(parse_row_id(cells[0]), values)
    return table


def parse_row_id(cell):
    try:
        return int(cell)
    except ValueError:
        raise TableError("bad row id %r" % (cell,))
