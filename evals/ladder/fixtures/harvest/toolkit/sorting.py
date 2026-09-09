"""Stable ordering helpers so reports never depend on hash order."""


def sorted_by(items, key, descending=False):
    """A stable sort that keeps the original order for equal keys."""
    return sorted(items, key=key, reverse=descending)


def top_n(items, key, count):
    """The `count` largest items by `key`, ties broken by original order."""
    if count <= 0:
        return []
    return sorted_by(items, key=key, descending=True)[:count]


def partition(items, predicate):
    """Split into (matching, rest), both in the original order."""
    matching = []
    rest = []
    for item in items:
        (matching if predicate(item) else rest).append(item)
    return matching, rest


def unique(items, key=None):
    seen = set()
    out = []
    for item in items:
        marker = key(item) if key else item
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out
