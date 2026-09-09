"""Identifier allocation.

Ids look like ``rec-0001``: a short alphabetic prefix, a dash, and a
zero-padded counter.  Zero padding means ids sort in insertion order for
the first ``10 ** width`` records; :func:`sort_key` keeps the ordering
correct after that, and tolerates ids imported from elsewhere.
"""

import re

from .errors import SchemaError

DEFAULT_PREFIX = "rec"
DEFAULT_WIDTH = 4
ID_PATTERN = re.compile(r"^([a-z][a-z0-9]*)-([0-9]+)$")


class IdAllocator:
    """Hands out the next free id for one store."""

    def __init__(self, prefix=DEFAULT_PREFIX, width=DEFAULT_WIDTH):
        if not isinstance(prefix, str) or not prefix.isalnum():
            raise SchemaError("bad id prefix %r" % (prefix,))
        if not prefix[:1].isalpha():
            raise SchemaError("id prefixes must start with a letter")
        if width < 1:
            raise SchemaError("id width must be positive")
        self.prefix = prefix.lower()
        self.width = width
        self._counter = 0

    def next_id(self):
        self._counter += 1
        return "%s-%0*d" % (self.prefix, self.width, self._counter)

    def reserve(self, record_id):
        """Push the counter past an id that was supplied from outside.

        Returns whether the id belonged to this allocator's own series.
        """
        parsed = parse_id(record_id)
        if parsed is None:
            return False
        prefix, number = parsed
        if prefix != self.prefix:
            return False
        if number > self._counter:
            self._counter = number
        return True

    @property
    def issued(self):
        return self._counter


def parse_id(record_id):
    """Split an id into ``(prefix, number)``, or ``None`` if it is foreign."""
    if not isinstance(record_id, str):
        return None
    match = ID_PATTERN.match(record_id)
    if match is None:
        return None
    return match.group(1), int(match.group(2))


def is_valid_id(record_id):
    return parse_id(record_id) is not None


def sort_key(record_id):
    """Order ids by prefix and then numerically.

    Foreign ids sort before generated ones and fall back to plain string
    ordering among themselves, so the result is always deterministic.
    """
    parsed = parse_id(record_id)
    if parsed is None:
        return ("", 0, record_id)
    prefix, number = parsed
    return (prefix, number, "")
