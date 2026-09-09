"""Query-string parsing without any dependency on urllib's mutable API."""

_HEX = "0123456789abcdefABCDEF"


def unquote(text):
    """Decode percent escapes and ``+`` separators in a query fragment."""
    text = text.replace("+", " ")
    if "%" not in text:
        return text
    out = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "%" and index + 2 < len(text) + 1:
            escape = text[index + 1:index + 3]
            if len(escape) == 2 and escape[0] in _HEX and escape[1] in _HEX:
                out.append(chr(int(escape, 16)))
                index += 3
                continue
        out.append(char)
        index += 1
    return "".join(out)


def parse_query_string(raw):
    """Return a list of ``(name, value)`` pairs in the order they appear."""
    if not raw:
        return []
    if raw.startswith("?"):
        raw = raw[1:]
    pairs = []
    for chunk in raw.replace(";", "&").split("&"):
        if not chunk:
            continue
        name, sep, value = chunk.partition("=")
        if not sep and not name:
            continue
        pairs.append((unquote(name), unquote(value)))
    return pairs


class QueryParams:
    """Read-only view over the parsed query string."""

    def __init__(self, raw=""):
        self.raw = raw or ""
        self._pairs = parse_query_string(self.raw)

    def __contains__(self, name):
        return any(key == name for key, _ in self._pairs)

    def __len__(self):
        return len(self._pairs)

    def __iter__(self):
        return iter(self._pairs)

    def get(self, name, default=None):
        for key, value in self._pairs:
            if key == name:
                return value
        return default

    def get_all(self, name):
        return [value for key, value in self._pairs if key == name]

    def get_int(self, name, default=None):
        value = self.get(name)
        if value is None or not value.strip():
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_bool(self, name, default=False):
        value = self.get(name)
        if value is None:
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")

    def items(self):
        return list(self._pairs)

    def to_dict(self):
        """Collapse repeated names, keeping the first value for each."""
        collapsed = {}
        for key, value in self._pairs:
            collapsed.setdefault(key, value)
        return collapsed

    def __repr__(self):
        return "QueryParams(%r)" % (self.raw,)
