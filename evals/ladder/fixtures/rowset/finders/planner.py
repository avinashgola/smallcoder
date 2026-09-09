"""Choosing how to answer a condition.

:func:`candidate_ids` looks at a condition and asks the table whether an
index can narrow it down.  It returns *candidates*, never answers: the
ids it hands back are re-checked against the condition before they reach
the caller, so an index that returns too much only costs time.  An index
that returns too little, on the other hand, is a wrong answer - which is
why an index may only be used when it covers the whole condition.

``None`` means "no index helped, walk the rows".
"""

from .conditions import (
    AtLeast,
    AtMost,
    Condition,
    Equals,
    EveryOf,
    InRange,
    OneOf,
)
from .results import RowSet
from .scan import check_ids, scan_ids


def candidate_ids(table, condition):
    """Ids an index can offer for ``condition``, or ``None``."""
    if isinstance(condition, Equals):
        index = _equality_index(table, condition.column, [condition.value])
        if index is None:
            return None
        return index.ids_for(condition.value)
    if isinstance(condition, OneOf):
        index = _equality_index(table, condition.column, condition.values)
        if index is None or not hasattr(index, "ids_for_any"):
            return None
        return index.ids_for_any(condition.values)
    if isinstance(condition, InRange):
        index = table.ordered_index(condition.column)
        if index is None:
            return None
        # The condition is a closed interval, and so is ``between``.
        return index.between(condition.low, condition.high)
    if isinstance(condition, AtLeast):
        index = table.ordered_index(condition.column)
        if index is None:
            return None
        return index.at_least(condition.low)
    if isinstance(condition, AtMost):
        index = table.ordered_index(condition.column)
        if index is None:
            return None
        return index.at_most(condition.high)
    if isinstance(condition, EveryOf):
        return _narrowest(table, condition)
    return None


def _equality_index(table, column, values):
    """An index able to answer equality for ``values``, or ``None``.

    An ordered index leaves empty cells out, so it cannot say which rows
    have none; that question has to go to a scan.
    """
    index = table.lookup_index(column)
    if index is None:
        return None
    if index.ordered and any(value is None for value in values):
        return None
    return index


def _narrowest(table, group):
    """Intersect whatever candidates the parts of an AND can supply."""
    best = None
    for part in group.parts:
        candidates = candidate_ids(table, part)
        if candidates is None:
            continue
        if best is None:
            best = set(candidates)
        else:
            best &= set(candidates)
    if best is None:
        return None
    return sorted(best)


def plan(table, condition):
    """Describe how ``condition`` would be answered, for tests and logs."""
    candidates = candidate_ids(table, condition)
    if candidates is None:
        return {"strategy": "scan", "candidates": len(table)}
    return {"strategy": "index", "candidates": len(candidates)}


def matching_ids(table, condition):
    """The ids that really match, whichever route was taken."""
    if not isinstance(condition, Condition):
        raise TypeError("expected a Condition, got %r" % (condition,))
    candidates = candidate_ids(table, condition)
    if candidates is None:
        return scan_ids(table, condition)
    return check_ids(table, condition, candidates)


def select(table, condition, order=None, descending=False, limit=None):
    """Run ``condition`` against ``table`` and return a :class:`RowSet`."""
    row_ids = matching_ids(table, condition)
    result = RowSet(table, row_ids)
    if order is not None:
        result = result.order_by(order, descending=descending)
    if limit is not None:
        result = result.limit(limit)
    return result
