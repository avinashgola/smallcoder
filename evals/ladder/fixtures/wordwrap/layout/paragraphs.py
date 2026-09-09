"""Split documents into paragraphs and wrap each one independently."""

from wrapping.filler import DEFAULT_WIDTH, wrap


def split_paragraphs(text):
    """Split `text` on blank lines, joining the lines of each paragraph."""
    paragraphs = []
    buffer = []
    for line in text.splitlines():
        if line.strip():
            buffer.append(line.strip())
        elif buffer:
            paragraphs.append(" ".join(buffer))
            buffer = []
    if buffer:
        paragraphs.append(" ".join(buffer))
    return paragraphs


def wrap_paragraphs(text, width=DEFAULT_WIDTH):
    """Wrap every paragraph; returns one list of lines per paragraph."""
    return [wrap(paragraph, width) for paragraph in split_paragraphs(text)]


def format_document(text, width=DEFAULT_WIDTH, gap=1):
    """Render a whole document, separating paragraphs by `gap` blank lines."""
    if gap < 0:
        raise ValueError("gap must not be negative")
    blocks = ["\n".join(lines) for lines in wrap_paragraphs(text, width)]
    return ("\n" * (gap + 1)).join(blocks)


def count_words(text):
    """Total number of words across every paragraph in `text`."""
    return sum(len(paragraph.split()) for paragraph in split_paragraphs(text))
