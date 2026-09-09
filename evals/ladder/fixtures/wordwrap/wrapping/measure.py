"""Work out how many columns a piece of text occupies."""

TAB_SIZE = 4
ELLIPSIS = "..."

# Characters that take up no width when printed to a terminal.
ZERO_WIDTH = frozenset("\x00\x07\x08\r\u200b\ufeff")


def expand_tabs(text, tab_size=TAB_SIZE):
    """Replace tabs with spaces, advancing to the next tab stop each time."""
    if tab_size <= 0:
        raise ValueError("tab_size must be positive")
    out = []
    column = 0
    for char in text:
        if char == "\t":
            fill_count = tab_size - (column % tab_size)
            out.append(" " * fill_count)
            column += fill_count
        elif char == "\n":
            out.append(char)
            column = 0
        else:
            out.append(char)
            column += 1
    return "".join(out)


def strip_zero_width(text):
    """Drop characters that occupy no columns on screen."""
    return "".join(char for char in text if char not in ZERO_WIDTH)


def display_width(text):
    """Columns `text` occupies once tabs are expanded and junk removed."""
    return len(strip_zero_width(expand_tabs(text)))


def truncate(text, width, marker=ELLIPSIS):
    """Shorten `text` to `width` columns, ending with `marker` when cut."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= len(marker):
        return text[:width]
    return text[: width - len(marker)] + marker


def pad(text, width, align="left", filler=" "):
    """Pad `text` out to `width` columns using the requested alignment."""
    if align not in ("left", "right", "center"):
        raise ValueError("unknown alignment: %s" % align)
    missing = width - display_width(text)
    if missing <= 0:
        return text
    if align == "left":
        return text + filler * missing
    if align == "right":
        return filler * missing + text
    left = missing // 2
    return filler * left + text + filler * (missing - left)
