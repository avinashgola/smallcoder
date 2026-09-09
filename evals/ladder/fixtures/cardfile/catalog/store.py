"""The catalogue store: records in, records out, indexes kept honest.

The store keeps three things in agreement with each other:

* ``_records``  id -> record, the authoritative copy
* ``_order``    the ids in insertion order, so results are reproducible
* ``_indexes``  the secondary indexes, refreshed on every write

Callers never receive the stored dictionaries themselves.  Reads hand
back copies, which is what keeps an index from drifting out of step with
a record that somebody mutated behind the store's back.
"""

from .changes import normalize_changes
from .errors import RecordNotFound, SchemaError
from .events import EventLog
from .ids import IdAllocator, is_valid_id, sort_key
from .indexing.registry import IndexRegistry
from .records import copy_record, normalize_record, project


class Store:
    """An ordered, in-memory collection of records."""

    def __init__(self, prefix="rec"):
        self._records = {}
        self._order = []
        self._ids = IdAllocator(prefix)
        self._indexes = IndexRegistry()
        self.events = EventLog()

    # ------------------------------------------------------------------
    # indexes
    # ------------------------------------------------------------------
    def add_index(self, field, unique=False, multi=False):
        """Define an index and backfill it from the records already stored."""
        index = self._indexes.add(field, unique=unique, multi=multi)
        for record_id in self._order:
            index.add(record_id, self._records[record_id])
        return index

    def drop_index(self, field):
        self._indexes.drop(field)

    def indexed_fields(self):
        return self._indexes.fields()

    def rebuild_indexes(self):
        """Refill every index from the records, discarding what was there."""
        self._indexes.rebuild((rid, self._records[rid]) for rid in self._order)

    def index_summary(self):
        return self._indexes.summary()

    def describe_indexes(self):
        """The index definitions, in the form :meth:`add_index` accepts."""
        described = []
        for field in self._indexes.fields():
            index = self._indexes.get(field)
            described.append(
                {"field": field, "unique": bool(index.unique), "multi": bool(index.multi)}
            )
        return described

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------
    def insert(self, values, record_id=None):
        """Store a new record and return the id it was filed under."""
        record = normalize_record(values)
        if record_id is None:
            record_id = self._ids.next_id()
        else:
            if not isinstance(record_id, str) or not record_id:
                raise SchemaError("explicit ids must be non-empty strings")
            if record_id in self._records:
                raise SchemaError("id %r is already in use" % (record_id,))
            if is_valid_id(record_id):
                self._ids.reserve(record_id)
        self._records[record_id] = record
        self._order.append(record_id)
        self._indexes.index_record(record_id, record)
        self.events.append("inserted", record_id)
        return record_id

    def insert_many(self, rows):
        """Insert several records, returning their ids in the same order."""
        return [self.insert(row) for row in rows]

    def update(self, record_id, changes):
        """Apply ``changes`` to a stored record and refresh the indexes.

        Only the fields named in ``changes`` are touched; everything else
        is left as it was.  The updated record is returned as a copy.
        """
        current = self._records.get(record_id)
        if current is None:
            raise RecordNotFound(record_id)
        patch = normalize_changes(changes)
        current.update(patch)
        self._indexes.reindex(record_id, current, current)
        self.events.append("updated", record_id)
        return copy_record(current)

    def replace(self, record_id, values):
        """Swap the whole body of a record, keeping its id and position."""
        current = self._records.get(record_id)
        if current is None:
            raise RecordNotFound(record_id)
        previous = copy_record(current)
        record = normalize_record(values)
        self._records[record_id] = record
        self._indexes.reindex(record_id, previous, record)
        self.events.append("replaced", record_id)
        return copy_record(record)

    def delete(self, record_id):
        """Remove a record and return the copy that was stored."""
        record = self._records.pop(record_id, None)
        if record is None:
            raise RecordNotFound(record_id)
        self._order.remove(record_id)
        self._indexes.unindex_record(record_id, record)
        self.events.append("deleted", record_id)
        return copy_record(record)

    def delete_where(self, field, value):
        """Delete every record whose ``field`` equals ``value``."""
        removed = self.find_ids(field, value)
        for record_id in removed:
            self.delete(record_id)
        return removed

    def clear(self):
        self._records = {}
        self._order = []
        self._indexes.clear()
        self.events.clear()

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------
    def get(self, record_id):
        record = self._records.get(record_id)
        if record is None:
            raise RecordNotFound(record_id)
        return copy_record(record)

    def peek(self, record_id, default=None):
        """Like :meth:`get` but returns ``default`` for an unknown id."""
        record = self._records.get(record_id)
        return default if record is None else copy_record(record)

    def ids(self):
        return list(self._order)

    def all(self):
        return [copy_record(self._records[rid]) for rid in self._order]

    def items(self):
        return [(rid, copy_record(self._records[rid])) for rid in self._order]

    def rows(self, fields=None):
        """Records with their id folded in, optionally projected."""
        out = []
        for record_id in self._order:
            record = self._records[record_id]
            body = project(record, fields) if fields else copy_record(record)
            body["id"] = record_id
            out.append(body)
        return out

    def values_of(self, field):
        """The distinct values stored in ``field``, in a stable order."""
        seen = []
        for record_id in self._order:
            value = self._records[record_id].get(field)
            if value not in seen:
                seen.append(value)
        return seen

    # ------------------------------------------------------------------
    # lookups
    # ------------------------------------------------------------------
    def find_ids(self, field, value):
        """Ids whose ``field`` equals ``value``.

        An indexed field is answered from the index; anything else falls
        back to a scan in insertion order.  Both paths return ids in the
        same order so callers cannot tell the two apart.
        """
        if self._indexes.has(field):
            return sorted(self._indexes.lookup(field, value), key=sort_key)
        return [rid for rid in self._order if self._records[rid].get(field) == value]

    def find(self, field, value):
        return [copy_record(self._records[rid]) for rid in self.find_ids(field, value)]

    def find_one(self, field, value):
        found = self.find_ids(field, value)
        return None if not found else copy_record(self._records[found[0]])

    def count_where(self, field, value):
        return len(self.find_ids(field, value))

    def __len__(self):
        return len(self._order)

    def __contains__(self, record_id):
        return record_id in self._records

    def __iter__(self):
        return iter(self.all())

    def __repr__(self):
        return "Store(records=%d, indexes=%s)" % (len(self._order), self._indexes.fields())
