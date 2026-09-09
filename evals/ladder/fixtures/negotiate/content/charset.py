"""Body encoding."""

SUPPORTED = ("utf-8", "utf-16", "ascii", "latin-1")
DEFAULT = "utf-8"


class UnsupportedCharset(ValueError):
    """Raised when a caller asks for an encoding the server does not have."""


def canonical(name):
    """Normalise a charset name, e.g. ``UTF8`` -> ``utf-8``."""
    if not name:
        return DEFAULT
    cleaned = name.strip().lower().replace("_", "-")
    aliases = {"utf8": "utf-8", "utf16": "utf-16", "us-ascii": "ascii",
               "iso-8859-1": "latin-1"}
    return aliases.get(cleaned, cleaned)


def is_supported(name):
    return canonical(name) in SUPPORTED


def encode(text, charset=DEFAULT):
    """Encode ``text``, raising a clear error for unknown charsets."""
    name = canonical(charset)
    if name not in SUPPORTED:
        raise UnsupportedCharset(charset)
    return text.encode(name)


def decode(data, charset=DEFAULT):
    name = canonical(charset)
    if name not in SUPPORTED:
        raise UnsupportedCharset(charset)
    return data.decode(name, "replace")
