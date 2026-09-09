"""Text shaping helpers used by the console reporter."""


def indent(text, prefix="  "):
    """Prefix every non-empty line of `text`."""
    lines = text.splitlines()
    return "\n".join(prefix + line if line.strip() else line for line in lines)


def truncate(text, limit):
    """Cut `text` to `limit` characters, marking the cut with an ellipsis."""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def plural(count, singular, suffix="s"):
    """'1 job' / '3 jobs' without dragging in a whole i18n layer."""
    word = singular if count == 1 else singular + suffix
    return "%d %s" % (count, word)


def joined(items, conjunction="and"):
    """Human readable list: 'a', 'a and b', 'a, b and c'."""
    items = [str(item) for item in items]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return "%s %s %s" % (", ".join(items[:-1]), conjunction, items[-1])
