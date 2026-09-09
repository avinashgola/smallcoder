"""Build predicates from plain dictionaries.

The dialect is small on purpose::

    {"status": "open"}                       exact match
    {"score": {"$gte": 10, "$lt": 50}}       comparisons
    {"tags": {"$contains": "urgent"}}        substring or membership
    {"owner": {"$in": ["ana", "bo"]}}        one of
    {"$or": [{"status": "open"}, ...]}       alternatives
    {"$not": {"status": "done"}}             negation

Anything else raises :class:`~catalog.errors.QueryError` rather than
matching everything by accident.
"""

from catalog.errors import QueryError

from .predicates import (
    All,
    Always,
    Any,
    Between,
    Compare,
    Contains,
    Eq,
    In,
    Ne,
    Not,
    Present,
    StartsWith,
)

COMPARISONS = ("$lt", "$lte", "$gt", "$gte")


def build_predicate(spec):
    """Turn a query specification into a single predicate."""
    if spec is None:
        return Always()
    if not isinstance(spec, dict):
        raise QueryError("query specifications must be mappings")
    parts = []
    for name, condition in spec.items():
        if name == "$or":
            parts.append(Any(build_predicate(item) for item in _as_list(condition)))
        elif name == "$and":
            parts.append(All(build_predicate(item) for item in _as_list(condition)))
        elif name == "$not":
            parts.append(Not(build_predicate(condition)))
        elif name.startswith("$"):
            raise QueryError("unknown top-level operator %r" % (name,))
        else:
            parts.extend(_field_predicates(name, condition))
    if not parts:
        return Always()
    if len(parts) == 1:
        return parts[0]
    return All(parts)


def _as_list(condition):
    if not isinstance(condition, (list, tuple)):
        raise QueryError("expected a list of sub-queries")
    if not condition:
        raise QueryError("an empty sub-query list would match nothing")
    return list(condition)


def _field_predicates(field, condition):
    if not isinstance(condition, dict):
        return [Eq(field, condition)]
    parts = []
    for operator, operand in condition.items():
        if operator in COMPARISONS:
            parts.append(Compare(field, operator[1:], operand))
        elif operator == "$eq":
            parts.append(Eq(field, operand))
        elif operator == "$ne":
            parts.append(Ne(field, operand))
        elif operator == "$in":
            parts.append(In(field, operand))
        elif operator == "$between":
            low, high = operand
            parts.append(Between(field, low, high))
        elif operator == "$contains":
            parts.append(Contains(field, operand))
        elif operator == "$startswith":
            parts.append(StartsWith(field, operand))
        elif operator == "$present":
            present = Present(field)
            parts.append(present if operand else Not(present))
        else:
            raise QueryError("unknown operator %r on field %r" % (operator, field))
    if not parts:
        raise QueryError("empty condition on field %r" % (field,))
    return parts
