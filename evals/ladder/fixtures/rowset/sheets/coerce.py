"""Coercing incoming values to a column's declared type.

The rules are deliberately narrow.  Anything ambiguous - the string
``"maybe"`` in a boolean column, a float with a fractional part in an
integer column - is refused rather than guessed at, because a table that
quietly rounds is worse than one that complains.
"""

from .errors import ValueError_

KINDS = ("text", "int", "float", "bool")
TRUE_WORDS = ("true", "yes", "y", "1", "on")
FALSE_WORDS = ("false", "no", "n", "0", "off")


def coerce(column, value, kind):
    """Return ``value`` as ``kind``, or raise :class:`ValueError_`."""
    if value is None:
        return None
    if kind == "text":
        return to_text(column, value)
    if kind == "int":
        return to_int(column, value)
    if kind == "float":
        return to_float(column, value)
    if kind == "bool":
        return to_bool(column, value)
    raise ValueError_(column, value, kind)


def to_text(column, value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError_(column, value, "text")


def to_int(column, value):
    if isinstance(value, bool):
        raise ValueError_(column, value, "int")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != int(value):
            raise ValueError_(column, value, "int")
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return int(text)
        except ValueError:
            raise ValueError_(column, value, "int")
    raise ValueError_(column, value, "int")


def to_float(column, value):
    if isinstance(value, bool):
        raise ValueError_(column, value, "float")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            raise ValueError_(column, value, "float")
    raise ValueError_(column, value, "float")


def to_bool(column, value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in TRUE_WORDS:
            return True
        if text in FALSE_WORDS:
            return False
    raise ValueError_(column, value, "bool")


def is_comparable(kind):
    """Whether values of ``kind`` may be used as ordered index keys."""
    return kind in ("int", "float", "text")
