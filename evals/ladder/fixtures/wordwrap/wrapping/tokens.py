"""Turn raw text into the words a line filler can place."""

from .measure import expand_tabs, strip_zero_width

# A hyphenated word may be broken after any of these when it is too long.
BREAK_AFTER = "-/"


def normalize(text):
    """Collapse every run of whitespace down to a single space."""
    return " ".join(strip_zero_width(expand_tabs(text)).split())


def split_words(text):
    """Split `text` into words, ignoring leading and trailing whitespace."""
    cleaned = normalize(text)
    if not cleaned:
        return []
    return cleaned.split(" ")


def break_long_word(word, width):
    """Chop a word that cannot fit on a line into `width`-sized pieces."""
    if width <= 0:
        raise ValueError("width must be positive")
    pieces = []
    start = 0
    while start < len(word):
        stop = min(start + width, len(word))
        # Prefer breaking just after a hyphen or slash if there is one in range.
        if stop < len(word):
            for index in range(stop - 1, start, -1):
                if word[index] in BREAK_AFTER:
                    stop = index + 1
                    break
        pieces.append(word[start:stop])
        start = stop
    return pieces


def prepare(text, width):
    """Words ready for filling; anything wider than a line is pre-split."""
    words = []
    for word in split_words(text):
        if len(word) > width:
            words.extend(break_long_word(word, width))
        else:
            words.append(word)
    return words
