"""The two comment lines at the top of a dump."""

from sheets.coerce import KINDS
from sheets.columns import Column
from sheets.errors import TableError

MAGIC = "rowset"
VERSION = 1
ID_COLUMN = "id"


def format_header(table):
    """The magic line and the column line for ``table``."""
    columns = []
    for column in table.columns:
        marker = "!" if column.required else ""
        columns.append("%s:%s%s" % (column.name, column.kind, marker))
    return [
        "# %s %d %s" % (MAGIC, VERSION, table.name),
        "#! " + "\t".join([ID_COLUMN] + columns),
    ]


def parse_header(lines):
    """Read the two header lines back into ``(name, columns)``."""
    if len(lines) < 2:
        raise TableError("a dump needs both header lines")
    magic = lines[0].strip()
    if not magic.startswith("# "):
        raise TableError("missing magic line")
    parts = magic[2:].split(" ", 2)
    if len(parts) != 3 or parts[0] != MAGIC:
        raise TableError("this is not a rowset dump")
    if parts[1] != str(VERSION):
        raise TableError("unsupported dump version %r" % (parts[1],))
    name = parts[2]
    columns_line = lines[1].strip()
    if not columns_line.startswith("#!"):
        raise TableError("missing column line")
    fields = columns_line[2:].strip().split("\t")
    if not fields or fields[0] != ID_COLUMN:
        raise TableError("the first column of a dump must be %r" % (ID_COLUMN,))
    return name, [parse_column(field) for field in fields[1:]]


def parse_column(field):
    """Turn ``"score:int!"`` back into a :class:`~sheets.columns.Column`."""
    text = field.strip()
    required = text.endswith("!")
    if required:
        text = text[:-1]
    if ":" not in text:
        raise TableError("column %r is missing its type" % (field,))
    name, kind = text.rsplit(":", 1)
    if kind not in KINDS:
        raise TableError("unknown column type %r" % (kind,))
    return Column(name, kind, required=required)
