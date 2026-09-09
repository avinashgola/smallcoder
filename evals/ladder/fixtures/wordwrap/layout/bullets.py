"""Render bullet and numbered lists with properly aligned continuations."""

from wrapping.filler import DEFAULT_WIDTH, wrap

from .indent import hanging_indent

BULLET = "- "


def bullet_list(items, width=DEFAULT_WIDTH, bullet=BULLET):
    """Wrap each item, indenting continuation lines under the first word."""
    lines = []
    for item in items:
        body = wrap(item, width - len(bullet)) or [""]
        lines.extend(hanging_indent(body, bullet, " " * len(bullet)))
    return lines


def numbered_list(items, width=DEFAULT_WIDTH, start=1):
    """Like `bullet_list`, but with right-aligned numbers as markers."""
    last = start + len(items) - 1
    marker_width = len(str(last)) + 2
    lines = []
    for offset, item in enumerate(items):
        marker = ("%d." % (start + offset)).rjust(marker_width - 1) + " "
        body = wrap(item, width - marker_width) or [""]
        lines.extend(hanging_indent(body, marker, " " * marker_width))
    return lines
