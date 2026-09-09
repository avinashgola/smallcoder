"""rowset - a tiny in-memory table with typed columns and indexes.

A :class:`~sheets.table.Table` holds rows keyed by an integer row id.
Columns are declared up front so values can be coerced on the way in and
so an ordered index knows its keys are comparable.

    table = Table("tickets", [Column("title", "text"), Column("score", "int")])
    table.add_index("score", ordered=True)
    table.add_row({"title": "Bleed the radiators", "score": 30})
"""

from .columns import Column, ColumnSet
from .errors import ColumnError, RowNotFound, TableError, ValueError_ as CoercionError
from .table import Table

__all__ = [
    "Table",
    "Column",
    "ColumnSet",
    "TableError",
    "ColumnError",
    "RowNotFound",
    "CoercionError",
]
