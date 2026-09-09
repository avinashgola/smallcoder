"""Naming alignments and guessing the right one for a column."""

from .cells import center, left, right

LEFT = "left"
RIGHT = "right"
CENTER = "center"
ALIGNMENTS = (LEFT, RIGHT, CENTER)

PLACERS = {LEFT: left, RIGHT: right, CENTER: center}


def place(text, width, alignment=LEFT, filler=" "):
    """Put `text` into a `width`-wide cell using the named alignment."""
    if alignment not in PLACERS:
        raise ValueError("unknown alignment: %s" % alignment)
    return PLACERS[alignment](text, width, filler)


def looks_numeric(value):
    """True when a value should be treated as a number when aligning."""
    text = str(value).strip().replace(",", "")
    if text[:1] in ("-", "+"):
        text = text[1:]
    text = text.rstrip("%")
    if not text or text.count(".") > 1:
        return False
    return text.replace(".", "", 1).isdigit()


def detect_alignment(values):
    """Right-align a column when every value it holds looks numeric."""
    filled = [value for value in values if str(value).strip()]
    if not filled:
        return LEFT
    if all(looks_numeric(value) for value in filled):
        return RIGHT
    return LEFT
