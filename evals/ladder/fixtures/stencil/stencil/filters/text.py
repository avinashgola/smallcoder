"""String filters."""

TRUNCATE_AT = 30
MARKER = "..."

# Words that stay lower case unless they start the string.
MINOR_WORDS = frozenset(["a", "an", "and", "at", "for", "in", "of", "on", "or", "the"])


def upper(value):
    return str(value).upper()


def lower(value):
    return str(value).lower()


def trim(value):
    return str(value).strip()


def title(value):
    """Title-case a phrase, leaving short joining words lower case."""
    words = str(value).split()
    out = []
    for index, word in enumerate(words):
        if index and word.lower() in MINOR_WORDS:
            out.append(word.lower())
        else:
            out.append(word[:1].upper() + word[1:].lower())
    return " ".join(out)


def truncate(value, limit=TRUNCATE_AT, marker=MARKER):
    """Shorten a string, adding `marker` when anything was removed."""
    text = str(value)
    if len(text) <= limit:
        return text
    if limit <= len(marker):
        return text[:limit]
    return text[: limit - len(marker)].rstrip() + marker
