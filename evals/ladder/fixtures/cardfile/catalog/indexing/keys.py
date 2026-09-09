"""Turning record values into index keys.

Index keys have to be hashable and comparable so that buckets can be
looked up and listed in a stable order.  Records may hold lists and
dicts, so those are flattened into tuples on the way in.
"""

MISSING = "\x00missing"


def index_key(value):
    """Return a hashable, comparable key for ``value``.

    ``None`` and absent fields share the :data:`MISSING` key so that
    "has no owner" is a thing you can look up.
    """
    if value is None:
        return MISSING
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        return tuple(index_key(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, index_key(item)) for key, item in value.items()))
    return str(value)


def keys_for(record, field, multi=False):
    """Every key ``record`` contributes to the index on ``field``.

    A multi-valued index fans a list out into one key per element, which
    is how tag lookups work; an ordinary index files the list as a single
    composite key.  An empty list has nothing to file and lands under
    :data:`MISSING`.
    """
    if field not in record:
        return [MISSING]
    value = record[field]
    if multi and isinstance(value, (list, tuple)):
        if not value:
            return [MISSING]
        return [index_key(item) for item in value]
    return [index_key(value)]


def is_missing(key):
    return key == MISSING


def describe_key(key):
    """A short human-readable rendering of a key, for error messages."""
    if is_missing(key):
        return "<missing>"
    if isinstance(key, tuple):
        return "(" + ", ".join(describe_key(item) for item in key) + ")"
    return repr(key)
