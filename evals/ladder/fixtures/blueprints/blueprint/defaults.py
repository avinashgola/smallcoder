"""What an unset field looks like, and how to copy one.

The blank value for a list field is a list and for a map field a
dictionary - both mutable.  :func:`clone_default` makes the copy that
lets one blank value be handed out more than once.
"""

from .errors import FieldError

BLANKS = {
    "text": "",
    "number": 0,
    "flag": False,
    "list": [],
    "map": {},
}
KINDS = tuple(sorted(BLANKS))
CONTAINERS = ("list", "map")


def blank_for(kind):
    """A fresh blank value for ``kind``."""
    if kind not in BLANKS:
        raise FieldError("unknown field type %r" % (kind,))
    return clone_default(BLANKS[kind])


def clone_default(value):
    """Return a copy of ``value`` that shares no container with it."""
    if isinstance(value, list):
        return [clone_default(item) for item in value]
    if isinstance(value, dict):
        return {key: clone_default(item) for key, item in value.items()}
    return value


def is_container_kind(kind):
    return kind in CONTAINERS


def kind_of(value):
    """The field type that would hold ``value``, or ``None``."""
    if isinstance(value, bool):
        return "flag"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "map"
    return None
