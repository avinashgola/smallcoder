"""Parsing of parameterised header values such as ``a/b; q=0.8; level=1``.

Several headers share this grammar: Accept, Accept-Language, Content-Type and
Content-Disposition all hang parameters off a value with semicolons.
"""


def split_commas(header):
    """Split on commas that are not inside a quoted string."""
    if not header:
        return []
    parts = []
    current = []
    quoted = False
    for char in header:
        if char == '"':
            quoted = not quoted
            current.append(char)
        elif char == "," and not quoted:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"')
    return value


def split_params(value):
    """Return ``(head, params)`` for one semicolon separated value."""
    chunks = value.split(";")
    head = chunks[0].strip()
    params = {}
    for chunk in chunks[1:]:
        if "=" not in chunk:
            key, raw = chunk.strip(), ""
        else:
            key, _, raw = chunk.partition("=")
        key = key.strip().lower()
        if key:
            params[key] = unquote(raw)
    return head, params


def join_params(head, params):
    """The inverse of :func:`split_params`, with parameters sorted by name."""
    parts = [head]
    for key in sorted(params):
        value = params[key]
        if any(char in value for char in ' ;,"'):
            value = '"%s"' % value.replace('"', '\\"')
        parts.append("%s=%s" % (key, value))
    return "; ".join(parts)
