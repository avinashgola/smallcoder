"""Ordering entries.

Fields have no declared type, so a value that cannot be compared with
the rest would blow a sort up halfway through.  :func:`sort_key` maps
everything onto a tuple instead, and puts entries missing the field at
the end whichever direction the sort runs in.
"""

MISSING_RANK = 2
TEXT_RANK = 1
NUMBER_RANK = 0


def sort_key(value, present=True):
    if not present or value is None:
        return (MISSING_RANK, 0.0, "")
    if isinstance(value, bool):
        return (NUMBER_RANK, float(value), "")
    if isinstance(value, (int, float)):
        return (NUMBER_RANK, float(value), "")
    if isinstance(value, str):
        return (TEXT_RANK, 0.0, value)
    return (TEXT_RANK, 0.0, repr(value))


def by_field(entries, name, descending=False):
    """Sort by one field; entries without it come last either way."""
    with_field = [entry for entry in entries if entry.has(name)]
    without = [entry for entry in entries if not entry.has(name)]
    with_field.sort(key=lambda entry: sort_key(entry.get(name)), reverse=descending)
    return with_field + without


def by_revision(entries, descending=False):
    return sorted(entries, key=lambda entry: entry.revision, reverse=descending)


def by_id(entries, descending=False):
    return sorted(entries, key=lambda entry: entry.id, reverse=descending)


def newest_first(entries):
    """Most-amended entries first, ties broken by id for reproducibility."""
    return sorted(entries, key=lambda entry: (-entry.revision, entry.id))
