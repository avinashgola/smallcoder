"""Helpers for the dictionaries that flow between stages.

Stage bodies are ordinary functions taking a list of rows and returning a new
list; these are the operations they reach for most often.
"""


def keep(rows, predicate):
    """Rows for which `predicate` is true, in the original order."""
    return [row for row in rows if predicate(row)]


def drop_missing(rows, fields):
    """Rows that carry every one of `fields`."""
    fields = list(fields)
    return [row for row in rows if all(field in row for field in fields)]


def project(rows, fields):
    """Narrow every row to `fields`, skipping the ones it does not have."""
    fields = list(fields)
    return [{f: row[f] for f in fields if f in row} for row in rows]


def add_field(rows, name, compute):
    """A copy of every row with one extra computed field."""
    out = []
    for row in rows:
        new_row = dict(row)
        new_row[name] = compute(row)
        out.append(new_row)
    return out


def rename(rows, mapping):
    return [{mapping.get(k, k): v for k, v in row.items()} for row in rows]


def sum_field(rows, name, default=0.0):
    total = 0.0
    for row in rows:
        try:
            total += float(row.get(name, default))
        except (TypeError, ValueError):
            total += float(default)
    return round(total, 6)


def distinct_by(rows, field):
    """First row per distinct value of `field`, in the original order."""
    seen = set()
    out = []
    for row in rows:
        marker = row.get(field)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(row)
    return out
