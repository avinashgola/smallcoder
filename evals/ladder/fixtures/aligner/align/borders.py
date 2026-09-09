"""Rules and separators drawn between the cells of a table."""

CORNER = "+"
HORIZONTAL = "-"
VERTICAL = "|"
PADDING = 1


def rule(widths, padding=PADDING, corner=CORNER, horizontal=HORIZONTAL):
    """A `+------+----+` rule sized to the given column widths."""
    segments = [horizontal * (width + 2 * padding) for width in widths]
    return corner + corner.join(segments) + corner


def join_cells(cells, padding=PADDING, vertical=VERTICAL):
    """Join already-placed cells into one row, padding inside each cell."""
    space = " " * padding
    body = vertical.join(space + cell + space for cell in cells)
    return vertical + body + vertical


def row_width(widths, padding=PADDING):
    """Total printed width of a row with these column widths."""
    return sum(width + 2 * padding + 1 for width in widths) + 1
