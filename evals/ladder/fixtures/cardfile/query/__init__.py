"""Filtering, ordering and paging for catalogue records.

The query layer works on plain records - it never touches the store - so
the same predicates can be run against a snapshot, a list of rows or the
output of another query.

    from query import Query

    Query.from_spec({"status": "open"}).order_by("-score").limit(10).run(rows)
"""

from .engine import Query, run_spec
from .ordering import parse_order, sort_records
from .paging import page_count, slice_page
from .parser import build_predicate
from .predicates import All, Any, Between, Contains, Eq, In, Not, Predicate

__all__ = [
    "Query",
    "run_spec",
    "build_predicate",
    "Predicate",
    "Eq",
    "In",
    "Between",
    "Contains",
    "All",
    "Any",
    "Not",
    "sort_records",
    "parse_order",
    "slice_page",
    "page_count",
]
