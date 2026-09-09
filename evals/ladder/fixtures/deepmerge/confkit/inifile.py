"""A very small INI-style reader.

Sections become top-level keys and dotted option names become nested ones::

    [server]
    bind.port = 8080
    debug = false
"""

from .errors import ParseError
from .paths import assign

_TRUE = {"true", "yes", "on"}
_FALSE = {"false", "no", "off"}


def atom(raw):
    """Convert one right-hand side into a bool, number or string."""
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    lowered = text.lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def parse(text):
    """Parse INI text into a nested mapping."""
    data = {}
    section = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.split("#", 1)[0].split(";", 1)[0].strip()
        if not stripped:
            continue
        if stripped.startswith("["):
            if not stripped.endswith("]") or len(stripped) < 3:
                raise ParseError(number, "malformed section header")
            section = stripped[1:-1].strip()
            data.setdefault(section, {})
            continue
        if "=" not in stripped:
            raise ParseError(number, "expected key = value")
        key, _, raw = stripped.partition("=")
        key = key.strip()
        if not key:
            raise ParseError(number, "empty option name")
        path = key if section is None else f"{section}.{key}"
        data = assign(data, path, atom(raw))
    return data
