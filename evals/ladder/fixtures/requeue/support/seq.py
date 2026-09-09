"""Sequence helpers used while draining and reporting on queues."""


def chunked(items, size):
    """Split `items` into consecutive lists of at most `size` elements."""
    if size <= 0:
        raise ValueError("chunk size must be positive")
    items = list(items)
    return [items[start : start + size] for start in range(0, len(items), size)]


def first(items, default=None):
    for item in items:
        return item
    return default


def last(items, default=None):
    result = default
    for item in items:
        result = item
    return result


def take_while(items, predicate):
    out = []
    for item in items:
        if not predicate(item):
            break
        out.append(item)
    return out


def counts_by(items, key):
    """Count items per key, in first-seen key order."""
    totals = {}
    for item in items:
        name = key(item)
        totals[name] = totals.get(name, 0) + 1
    return totals
