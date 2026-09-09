"""Turning a result list into pages."""


def slice_page(rows, limit=None, offset=0):
    """Return the window ``rows[offset:offset + limit]``.

    A negative offset counts from the start rather than the end, which is
    almost never what a caller meant to ask for.
    """
    if offset < 0:
        offset = 0
    if limit is None:
        return list(rows[offset:])
    if limit < 0:
        raise ValueError("limit must not be negative")
    return list(rows[offset:offset + limit])


def page_count(total, per_page):
    """How many pages ``total`` rows fill."""
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    if total <= 0:
        return 0
    return (total + per_page - 1) // per_page


def page_of(rows, page, per_page):
    """One-based page ``page`` of ``rows``."""
    if page < 1:
        raise ValueError("pages are numbered from one")
    return slice_page(rows, limit=per_page, offset=(page - 1) * per_page)


def describe_page(total, page, per_page):
    """A ``(first, last, pages)`` summary for a result footer."""
    pages = page_count(total, per_page)
    if pages == 0 or page > pages:
        return (0, 0, pages)
    first = (page - 1) * per_page + 1
    last = min(page * per_page, total)
    return (first, last, pages)
