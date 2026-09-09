"""Turn raw environment strings into Python values."""

from .errors import CastError

TRUE_WORDS = frozenset({"1", "true", "yes", "on"})
FALSE_WORDS = frozenset({"0", "false", "no", "off"})


def to_str(raw):
    return raw.strip()


def to_bool(raw):
    text = raw.strip().lower()
    if text in TRUE_WORDS:
        return True
    if text in FALSE_WORDS:
        return False
    raise CastError("bool", raw)


def to_int(raw):
    try:
        return int(raw.strip(), 10)
    except ValueError:
        raise CastError("int", raw) from None


def to_float(raw):
    try:
        return float(raw.strip())
    except ValueError:
        raise CastError("float", raw) from None


def to_list(raw):
    """Comma separated items, ignoring blanks and surrounding space."""
    return tuple(item.strip() for item in raw.split(",") if item.strip())


CASTERS = {
    "str": to_str,
    "bool": to_bool,
    "int": to_int,
    "float": to_float,
    "list": to_list,
}


def cast(kind, raw, where=None):
    """Cast ``raw`` with the caster registered for ``kind``.

    ``where`` is the name of the variable the value came from; it only makes
    the error message useful.
    """
    if kind not in CASTERS:
        raise CastError(kind, raw, where)
    try:
        return CASTERS[kind](raw)
    except CastError as exc:
        raise CastError(kind, raw, where) from exc
