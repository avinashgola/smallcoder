"""Order preserving set operations.

The scheduler reports jobs in a stable order so that runs are reproducible;
plain sets would leak hash ordering into the output.
"""


def ordered_unique(items):
    """Return the items with duplicates removed, first occurrence wins."""
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def ordered_difference(items, removed):
    """Items that are not in `removed`, keeping the original order."""
    drop = set(removed)
    return [item for item in items if item not in drop]


def ordered_intersection(items, keep):
    """Items that also appear in `keep`, keeping the original order."""
    wanted = set(keep)
    return [item for item in items if item in wanted]


def group_by(items, key):
    """Bucket items by a key function, preserving insertion order."""
    buckets = {}
    for item in items:
        buckets.setdefault(key(item), []).append(item)
    return buckets
