"""Human readable rendering for logs and summaries."""


def seconds(value):
    """Compact duration: '0ms', '250ms', '1.5s', '2m05s'."""
    value = float(value)
    if value < 1:
        return "%dms" % round(value * 1000)
    if value < 60:
        return "%.1fs" % value
    minutes, rest = divmod(value, 60)
    return "%dm%02ds" % (int(minutes), int(rest))


def attempt_label(number, total=None):
    if total is None:
        return "attempt %d" % number
    return "attempt %d/%d" % (number, total)


def truncate(text, limit=60):
    text = str(text)
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def bullet_list(items, marker="-"):
    return "\n".join("%s %s" % (marker, item) for item in items)
