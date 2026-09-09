"""Deterministic ordering for query results.

Records are dictionaries with no schema, so a field can hold a number in
one record and a string in the next.  :func:`sort_value` maps values into
a tuple that always compares, which keeps sorting total and stable
instead of raising ``TypeError`` halfway through a result set.
"""

TYPE_RANK_NONE = 0
TYPE_RANK_NUMBER = 1
TYPE_RANK_TEXT = 2
TYPE_RANK_OTHER = 3


def sort_value(value):
    """Map ``value`` onto a tuple that is comparable with any other."""
    if value is None:
        return (TYPE_RANK_NONE, 0.0, "")
    if isinstance(value, bool):
        return (TYPE_RANK_NUMBER, float(value), "")
    if isinstance(value, (int, float)):
        return (TYPE_RANK_NUMBER, float(value), "")
    if isinstance(value, str):
        return (TYPE_RANK_TEXT, 0.0, value)
    return (TYPE_RANK_OTHER, 0.0, repr(value))


def parse_order(spec):
    """Turn ``"-score"`` or ``("score", True)`` into ``(field, descending)``."""
    if isinstance(spec, (list, tuple)):
        field, descending = spec
        return (field, bool(descending))
    if not isinstance(spec, str) or not spec.strip():
        raise ValueError("bad sort key %r" % (spec,))
    text = spec.strip()
    if text.startswith("-"):
        return (text[1:], True)
    if text.startswith("+"):
        return (text[1:], False)
    return (text, False)


def parse_orders(specs):
    if specs is None:
        return []
    if isinstance(specs, str):
        return [parse_order(specs)]
    return [parse_order(spec) for spec in specs]


def sort_records(records, keys):
    """Sort ``records`` by ``keys``, most significant key first.

    Each key is a ``(field, descending)`` pair.  Python's sort is stable,
    so the list is sorted by the least significant key first and the most
    significant key last; that is the only way to honour keys that run in
    different directions.
    """
    ordered = list(records)
    for field, descending in reversed(list(keys)):
        ordered.sort(key=lambda record: sort_value(record.get(field)), reverse=descending)
    return ordered


def order_by(records, specs):
    """Convenience wrapper: parse ``specs`` and sort in one step."""
    return sort_records(records, parse_orders(specs))
