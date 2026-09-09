"""Draw plain-ASCII boxes around wrapped text."""

from wrapping.filler import wrap
from wrapping.measure import pad, truncate

CORNER = "+"
HORIZONTAL = "-"
VERTICAL = "|"
MARGIN = 1


def _rule(inner):
    return CORNER + HORIZONTAL * (inner + 2 * MARGIN) + CORNER


def _row(content, inner, align="left"):
    space = " " * MARGIN
    return VERTICAL + space + pad(content, inner, align) + space + VERTICAL


def inner_width(width):
    """Columns available for content inside a box `width` columns wide."""
    inner = width - 2 - 2 * MARGIN
    if inner < 1:
        raise ValueError("width is too small for a box")
    return inner


def box(text, width=40):
    """Return the lines of a bordered box exactly `width` columns wide."""
    inner = inner_width(width)
    body = wrap(text, inner) or [""]
    return [_rule(inner)] + [_row(line, inner) for line in body] + [_rule(inner)]


def titled_box(title, text, width=40):
    """A box with a centred, upper-cased title above a horizontal rule."""
    inner = inner_width(width)
    heading = truncate(title.upper(), inner)
    rest = box(text, width)
    return [rest[0], _row(heading, inner, "center"), _rule(inner)] + rest[1:]
