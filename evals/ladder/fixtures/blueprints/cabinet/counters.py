"""Record ids.

Ids are ``<kind>-<number>``: the blueprint name, a dash and a counter
that runs per kind, so ``task-0001`` and ``note-0001`` can both exist.
Numbers are never reused, even after a record is deleted.
"""

import re

from blueprint.errors import BlueprintError

ID_PATTERN = re.compile(r"^([a-z][a-z0-9_]*)-([0-9]+)$")
DEFAULT_WIDTH = 4


class Counters:
    """One running number per kind of record."""

    def __init__(self, width=DEFAULT_WIDTH):
        if width < 1:
            raise BlueprintError("id width must be positive")
        self.width = width
        self._issued = {}

    def next_id(self, kind):
        number = self._issued.get(kind, 0) + 1
        self._issued[kind] = number
        return "%s-%0*d" % (kind, self.width, number)

    def observe(self, record_id):
        """Note an id read from a saved cabinet so it is not handed out again."""
        parsed = split_id(record_id)
        if parsed is None:
            return False
        kind, number = parsed
        if number > self._issued.get(kind, 0):
            self._issued[kind] = number
        return True

    def issued(self, kind):
        return self._issued.get(kind, 0)

    def kinds(self):
        return sorted(self._issued)


def split_id(record_id):
    """``("task", 1)`` for ``"task-0001"``, or ``None``."""
    if not isinstance(record_id, str):
        return None
    match = ID_PATTERN.match(record_id)
    if match is None:
        return None
    return match.group(1), int(match.group(2))


def kind_of_id(record_id):
    parsed = split_id(record_id)
    return None if parsed is None else parsed[0]


def id_sort_key(record_id):
    """Sort ids by kind and then numerically."""
    parsed = split_id(record_id)
    if parsed is None:
        return ("", 0, record_id)
    kind, number = parsed
    return (kind, number, "")
