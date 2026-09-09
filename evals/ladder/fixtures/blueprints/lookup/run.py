"""Running terms against a cabinet."""

from .terms import Term


def rows_of(cabinet, kind=None):
    """The rows a search runs over."""
    return cabinet.rows(kind)


def check(term):
    if not isinstance(term, Term):
        raise TypeError("expected a Term, got %r" % (term,))
    return term


def find(cabinet, term, kind=None):
    """Every matching row, in creation order."""
    check(term)
    return [row for row in rows_of(cabinet, kind) if term.holds(row)]


def find_ids(cabinet, term, kind=None):
    return [row["id"] for row in find(cabinet, term, kind)]


def find_one(cabinet, term, kind=None, default=None):
    found = find(cabinet, term, kind)
    return found[0] if found else default


def count(cabinet, term, kind=None):
    return len(find(cabinet, term, kind))


def tally(cabinet, name, kind=None):
    """``value -> how many records hold it`` for one field.

    Values that are containers are counted by their rendering, so the
    tally works on any field without blowing up on an unhashable one.
    """
    counts = {}
    for row in rows_of(cabinet, kind):
        value = row.get(name)
        key = repr(value) if isinstance(value, (list, dict)) else value
        counts[key] = counts.get(key, 0) + 1
    return counts
