"""Greedy line filling: put as many words on a line as will fit."""

from .tokens import prepare

DEFAULT_WIDTH = 72


def fill_lines(words, width):
    """Pack `words` into lines of at most `width` columns.

    Words are never reordered and a word is only moved to the next line when
    it genuinely does not fit on the current one.
    """
    if width <= 0:
        raise ValueError("width must be positive")
    lines = []
    current = []
    used = 0
    for word in words:
        gap = 1 if current else 0
        if current and used + gap + len(word) >= width:
            lines.append(" ".join(current))
            current = [word]
            used = len(word)
        else:
            current.append(word)
            used += gap + len(word)
    if current:
        lines.append(" ".join(current))
    return lines


def wrap(text, width=DEFAULT_WIDTH):
    """Wrap `text` and return the resulting lines."""
    return fill_lines(prepare(text, width), width)


def fill(text, width=DEFAULT_WIDTH):
    """Wrap `text` and join the lines back into a single string."""
    return "\n".join(wrap(text, width))


def shorten(text, width=DEFAULT_WIDTH, marker="..."):
    """Collapse `text` onto a single line, trimming it to `width` columns."""
    lines = wrap(text, width)
    if len(lines) <= 1:
        return lines[0] if lines else ""
    room = width - len(marker)
    joined = " ".join(lines)
    return joined[:room].rstrip() + marker
