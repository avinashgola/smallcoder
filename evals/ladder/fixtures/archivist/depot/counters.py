"""Entry ids and revision numbers.

Ids are ``e-0001`` style strings; revisions are plain integers starting
at one.  Both are handed out by the depot, never by the caller, so that
an entry's history is always a straight line.
"""

import re

from .errors import DepotError

ID_PATTERN = re.compile(r"^e-([0-9]{4,})$")
FIRST_REVISION = 1


class Counter:
    """Hands out ``e-0001``, ``e-0002``, ... for one depot."""

    def __init__(self, width=4):
        if width < 1:
            raise DepotError("id width must be positive")
        self.width = width
        self._issued = 0

    def next_id(self):
        self._issued += 1
        return "e-%0*d" % (self.width, self._issued)

    def observe(self, entry_id):
        """Take note of an id read from an archive, so it is not reissued."""
        number = id_number(entry_id)
        if number is None:
            return False
        if number > self._issued:
            self._issued = number
        return True

    @property
    def issued(self):
        return self._issued


def id_number(entry_id):
    """The numeric part of an id, or ``None`` when it is not one of ours."""
    if not isinstance(entry_id, str):
        return None
    match = ID_PATTERN.match(entry_id)
    if match is None:
        return None
    return int(match.group(1))


def is_entry_id(entry_id):
    return id_number(entry_id) is not None


def next_revision(revision):
    """The revision that follows ``revision``."""
    if not isinstance(revision, int) or isinstance(revision, bool):
        raise DepotError("revisions are integers, got %r" % (revision,))
    if revision < FIRST_REVISION:
        raise DepotError("revisions start at %d" % (FIRST_REVISION,))
    return revision + 1
