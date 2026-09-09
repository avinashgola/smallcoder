"""Path and query helpers shared by the router and the middleware."""


def normalize(path):
    """Collapse duplicate slashes and strip a trailing one."""
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def segments(path):
    return [part for part in normalize(path).split("/") if part]


def join(*parts):
    """Join path fragments with exactly one slash between them."""
    cleaned = [part.strip("/") for part in parts if part and part.strip("/")]
    return "/" + "/".join(cleaned) if cleaned else "/"


def starts_with(path, prefix):
    """Whether ``path`` lies at or below ``prefix``."""
    prefix = normalize(prefix)
    if prefix == "/":
        return True
    path = normalize(path)
    return path == prefix or path.startswith(prefix + "/")


def parse_query(raw):
    """Query string to ``(name, value)`` pairs, percent escapes decoded."""
    if not raw:
        return []
    if raw.startswith("?"):
        raw = raw[1:]
    pairs = []
    for chunk in raw.split("&"):
        if not chunk:
            continue
        name, _, value = chunk.partition("=")
        pairs.append((_decode(name), _decode(value)))
    return pairs


def _decode(text):
    text = text.replace("+", " ")
    if "%" not in text:
        return text
    out = []
    index = 0
    while index < len(text):
        if text[index] == "%" and index + 3 <= len(text):
            escape = text[index + 1:index + 3]
            try:
                out.append(chr(int(escape, 16)))
            except ValueError:
                out.append(text[index])
                index += 1
                continue
            index += 3
            continue
        out.append(text[index])
        index += 1
    return "".join(out)
