"""Ordering rows.

Fields are typed by their blueprint, but a search can run across kinds,
so a column may hold text in one row and a number in the next.
:func:`sort_key` maps every value onto a comparable tuple and puts empty
ones last whichever way the sort runs.
"""

from cabinet.counters import id_sort_key

EMPTY_RANK = 2
TEXT_RANK = 1
NUMBER_RANK = 0


def sort_key(value):
    if value is None:
        return (EMPTY_RANK, 0.0, "")
    if isinstance(value, bool):
        return (NUMBER_RANK, float(value), "")
    if isinstance(value, (int, float)):
        return (NUMBER_RANK, float(value), "")
    if isinstance(value, str):
        return (TEXT_RANK, 0.0, value)
    if isinstance(value, (list, dict)):
        return (NUMBER_RANK, float(len(value)), "")
    return (TEXT_RANK, 0.0, repr(value))


def ordered_by(rows, name, descending=False):
    """Sort rows by one field; rows without it come last either way."""
    present = [row for row in rows if name in row and row[name] is not None]
    absent = [row for row in rows if name not in row or row[name] is None]
    present.sort(key=lambda row: sort_key(row[name]), reverse=descending)
    return present + absent


def newest_first(rows):
    """Most recently created first, by id."""
    return sorted(rows, key=lambda row: id_sort_key(row["id"]), reverse=True)


def by_id(rows):
    return sorted(rows, key=lambda row: id_sort_key(row["id"]))
