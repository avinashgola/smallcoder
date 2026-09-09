"""Path helpers."""


def tidy(path):
    """A path with one leading slash, no doubles and no trailing slash."""
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def parts(path):
    return [part for part in tidy(path).split("/") if part]


def query_pairs(raw):
    """Parse a query string into ``(name, value)`` pairs."""
    if not raw:
        return []
    raw = raw[1:] if raw.startswith("?") else raw
    pairs = []
    for chunk in raw.split("&"):
        if not chunk:
            continue
        name, _, value = chunk.partition("=")
        pairs.append((percent_decode(name), percent_decode(value)))
    return pairs


def percent_decode(text):
    text = text.replace("+", " ")
    if "%" not in text:
        return text
    out = []
    index = 0
    while index < len(text):
        if text[index] == "%" and index + 3 <= len(text):
            try:
                out.append(chr(int(text[index + 1:index + 3], 16)))
            except ValueError:
                out.append(text[index])
                index += 1
                continue
            index += 3
        else:
            out.append(text[index])
            index += 1
    return "".join(out)
