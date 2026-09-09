"""Conditions, planning and result sets for querying a table.

    from finders import InRange, select

    select(table, InRange("score", 10, 30)).column("title")

Conditions describe *what* is wanted; the planner decides *how* to find
it, using an index when the table has a useful one and falling back to a
scan when it does not.  Either way the answer is the same.
"""

from .conditions import (
    AnyOf,
    AtLeast,
    AtMost,
    Condition,
    Equals,
    EveryOf,
    InRange,
    Matches,
    Negate,
    OneOf,
)
from .planner import candidate_ids, select
from .results import RowSet
from .scan import scan_ids, scan_rows

__all__ = [
    "Condition",
    "Equals",
    "OneOf",
    "InRange",
    "AtLeast",
    "AtMost",
    "Matches",
    "EveryOf",
    "AnyOf",
    "Negate",
    "select",
    "candidate_ids",
    "scan_ids",
    "scan_rows",
    "RowSet",
]
