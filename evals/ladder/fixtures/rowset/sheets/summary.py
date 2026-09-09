"""Small aggregations over a table or a list of rows.

Everything here ignores ``None`` rather than treating it as zero: a
column that is only half filled in should report the average of the
values that exist, not an average dragged towards nothing.
"""

from .errors import ColumnError


def values_of(rows, column):
    """The non-empty values of ``column`` across ``rows``."""
    found = []
    for row in rows:
        if column not in row:
            raise ColumnError("unknown column %r" % (column,))
        value = row[column]
        if value is not None:
            found.append(value)
    return found


def count_filled(rows, column):
    return len(values_of(rows, column))


def total(rows, column):
    return sum(values_of(rows, column))


def mean(rows, column):
    values = values_of(rows, column)
    if not values:
        return None
    return sum(values) / len(values)


def smallest(rows, column):
    values = values_of(rows, column)
    return min(values) if values else None


def largest(rows, column):
    values = values_of(rows, column)
    return max(values) if values else None


def count_by(rows, column):
    """``value -> how many rows hold it``, including ``None``."""
    tally = {}
    for row in rows:
        value = row.get(column)
        tally[value] = tally.get(value, 0) + 1
    return tally


def group_by(rows, column):
    """``value -> the rows holding it``, keeping insertion order."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row.get(column), []).append(row)
    return grouped


def describe(rows, column):
    """A small summary dictionary for a numeric column."""
    values = values_of(rows, column)
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "mean": (sum(values) / len(values)) if values else None,
    }
