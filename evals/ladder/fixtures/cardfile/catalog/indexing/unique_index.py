"""A unique secondary index: key -> exactly one record id."""

from ..errors import DuplicateKey
from .keys import MISSING, keys_for


class UniqueIndex:
    """Refuses to file two different records under the same key.

    Records that do not carry the field at all are simply not indexed,
    so a half-populated field can still be made unique.
    """

    unique = True

    def __init__(self, field):
        self.field = field
        self.multi = False
        self._entries = {}

    def add(self, record_id, record):
        for key in keys_for(record, self.field):
            if key == MISSING:
                continue
            holder = self._entries.get(key)
            if holder is not None and holder != record_id:
                raise DuplicateKey(self.field, key)
            self._entries[key] = record_id

    def remove(self, record_id, record):
        for key in keys_for(record, self.field):
            if self._entries.get(key) == record_id:
                del self._entries[key]

    def lookup(self, key):
        record_id = self._entries.get(key)
        return [] if record_id is None else [record_id]

    def holder(self, key):
        """The single id filed under ``key``, or ``None``."""
        return self._entries.get(key)

    def keys(self):
        return sorted(self._entries)

    def entries(self):
        return [(key, [self._entries[key]]) for key in self.keys()]

    def cardinality(self):
        return len(self._entries)

    def clear(self):
        self._entries = {}

    def __contains__(self, key):
        return key in self._entries

    def __len__(self):
        return len(self._entries)

    def __repr__(self):
        return "UniqueIndex(%r, keys=%d)" % (self.field, len(self._entries))
