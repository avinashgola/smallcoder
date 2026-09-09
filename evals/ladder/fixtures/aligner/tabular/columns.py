"""Decide how wide each column of a table has to be."""

from align.rules import detect_alignment

MIN_WIDTH = 1


def normalize_rows(rows, columns=None):
    """Turn every cell into a string and give every row the same length."""
    if columns is None:
        columns = max((len(row) for row in rows), default=0)
    normalized = []
    for row in rows:
        cells = [str(cell) for cell in row[:columns]]
        cells.extend("" for _ in range(columns - len(cells)))
        normalized.append(cells)
    return normalized


def column_values(rows, index):
    """Every value in one column, top to bottom."""
    return [row[index] for row in rows]


def column_widths(rows, minimum=MIN_WIDTH, maximum=None):
    """The width each column needs, clamped to `minimum` and `maximum`."""
    if not rows:
        return []
    widths = []
    for index in range(len(rows[0])):
        needed = max(len(cell) for cell in column_values(rows, index))
        needed = max(needed, minimum)
        if maximum is not None:
            needed = min(needed, maximum)
        widths.append(needed)
    return widths


def fit_widths(widths, total, minimum=MIN_WIDTH):
    """Shave columns off the widest one until the row fits in `total`."""
    widths = list(widths)
    while sum(widths) > total:
        widest = max(range(len(widths)), key=lambda index: widths[index])
        if widths[widest] <= minimum:
            break
        widths[widest] -= 1
    return widths


def detect_alignments(rows):
    """Guess an alignment for every column from the values it holds."""
    if not rows:
        return []
    return [
        detect_alignment(column_values(rows, index)) for index in range(len(rows[0]))
    ]
