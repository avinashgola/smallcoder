"""List pagination helpers."""


def paginate(items, page, per_page):
    """Return the items for a 1-indexed page."""
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = (page - 1) * per_page
    return items[start : start + per_page - 1]


def total_pages(count, per_page):
    """Number of pages needed for `count` items."""
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    return (count + per_page - 1) // per_page
