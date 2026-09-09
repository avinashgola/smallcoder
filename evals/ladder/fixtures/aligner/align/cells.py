"""Fit one piece of text into a field of a given width."""

ELLIPSIS = "..."


def clip(text, width, marker=ELLIPSIS):
    """Cut `text` down to `width` columns, marking anything that was lost."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= len(marker):
        return text[:width]
    return text[: width - len(marker)] + marker


def clip_middle(text, width, marker=ELLIPSIS):
    """Like `clip`, but keeps both ends and drops the middle instead."""
    if len(text) <= width:
        return text
    if width <= len(marker) + 1:
        return clip(text, width, marker)
    room = width - len(marker)
    head = room - room // 2
    return text[:head] + marker + text[len(text) - (room - head) :]


def left(text, width, filler=" "):
    """Put `text` at the start of a field `width` columns wide."""
    if len(text) >= width:
        return text
    return text + filler * (width - len(text))


def right(text, width, filler=" "):
    """Put `text` at the end of a field `width` columns wide."""
    if len(text) >= width:
        return text
    return filler * (width - len(text)) + text


def center(text, width, filler=" "):
    """Centre `text`, giving the odd column to the right-hand side."""
    if len(text) >= width:
        return text
    before = width - len(text) // 2
    return filler * before + text + filler * (width - len(text) - before)
