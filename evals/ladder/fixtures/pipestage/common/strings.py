"""String helpers used by stage names and report rendering."""


def slugify(text):
    """Lowercase, hyphen separated, safe for use as a stage name."""
    cleaned = []
    previous_dash = False
    for ch in str(text).strip().lower():
        if ch.isalnum():
            cleaned.append(ch)
            previous_dash = False
        elif not previous_dash and cleaned:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-")


def snake_case(text):
    return slugify(text).replace("-", "_")


def title_case(text):
    return " ".join(word.capitalize() for word in slugify(text).split("-"))


def truncate(text, limit=48):
    text = str(text)
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def pad(text, width):
    return truncate(str(text), width).ljust(width)
