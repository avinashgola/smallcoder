"""Keeps a store's secondary indexes in step with its records."""

from ..errors import QueryError
from .hash_index import HashIndex
from .keys import index_key
from .unique_index import UniqueIndex


class IndexRegistry:
    """Owns every index defined on one store and fans writes out to them."""

    def __init__(self):
        self._indexes = {}

    def add(self, field, unique=False, multi=False):
        if field in self._indexes:
            raise QueryError("field %r is already indexed" % (field,))
        if unique and multi:
            raise QueryError("a unique index cannot be multi-valued")
        index = UniqueIndex(field) if unique else HashIndex(field, multi=multi)
        self._indexes[field] = index
        return index

    def drop(self, field):
        self._indexes.pop(field, None)

    def has(self, field):
        return field in self._indexes

    def get(self, field):
        if field not in self._indexes:
            raise QueryError("no index on field %r" % (field,))
        return self._indexes[field]

    def fields(self):
        return sorted(self._indexes)

    def index_record(self, record_id, record):
        """File ``record_id`` under every key ``record`` produces."""
        for index in self._indexes.values():
            index.add(record_id, record)

    def unindex_record(self, record_id, record):
        """Withdraw ``record_id`` from every key ``record`` produces."""
        for index in self._indexes.values():
            index.remove(record_id, record)

    def reindex(self, record_id, previous, updated):
        """Move ``record_id`` from the keys of ``previous`` to those of ``updated``.

        ``previous`` has to be the record as it stood *before* the change:
        its keys are the ones that get withdrawn.  ``updated`` is the
        record afterwards and supplies the keys to file it under.
        """
        self.unindex_record(record_id, previous)
        self.index_record(record_id, updated)

    def lookup(self, field, value):
        """Ids filed under ``value`` in the index on ``field``."""
        return self.get(field).lookup(index_key(value))

    def rebuild(self, records):
        """Throw every index away and refill it from ``records``."""
        for index in self._indexes.values():
            index.clear()
        for record_id, record in records:
            self.index_record(record_id, record)

    def clear(self):
        for index in self._indexes.values():
            index.clear()

    def summary(self):
        """``field -> number of distinct keys``, handy when debugging."""
        return {field: index.cardinality() for field, index in self._indexes.items()}

    def __len__(self):
        return len(self._indexes)
