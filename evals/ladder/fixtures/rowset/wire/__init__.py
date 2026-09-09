"""A flat text format for saving and reloading a table.

The format is line oriented and tab separated so it stays readable in a
terminal and diffs sensibly in version control::

    # rowset 1 tickets
    #! id  title:text  score:int
    1   Bleed the radiators 30

The header carries the column types, which is what lets a reloaded table
coerce values the same way the original did.
"""

from .header import format_header, parse_header
from .parse import load_table, parse_cell
from .text import dump_table, format_cell

__all__ = [
    "dump_table",
    "load_table",
    "format_header",
    "parse_header",
    "format_cell",
    "parse_cell",
]
