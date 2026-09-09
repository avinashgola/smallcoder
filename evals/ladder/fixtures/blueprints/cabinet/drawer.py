"""The cabinet itself.

A cabinet holds records of several kinds side by side.  Every record is
built from the blueprint of its kind, so it always carries one entry per
declared field even when the caller supplied only a couple of them.

Reads hand out copies.  Writes go through the small operations in
:mod:`cabinet.mutate`, which check the field they are given before they
touch anything.
"""

from blueprint.errors import RecordNotFound, UnknownField, ValidationError
from blueprint.registry import Registry

from . import mutate
from .counters import Counters, id_sort_key
from .values import copy_record, only_fields


class Cabinet:
    """Records of several kinds, in the order they were created."""

    def __init__(self, registry=None):
        self._registry = registry if registry is not None else Registry()
        self._records = {}
        self._kinds = {}
        self._order = []
        self._counters = Counters()

    # ------------------------------------------------------------------
    # blueprints
    # ------------------------------------------------------------------
    def define(self, blueprint):
        """Register a blueprint so records of that kind can be created."""
        return self._registry.register(blueprint)

    def blueprint(self, kind):
        return self._registry.get(kind)

    def kinds(self):
        return self._registry.names()

    def field_of(self, record_id, name):
        """The declared field behind one of a record's values."""
        return self._registry.get(self.kind_of(record_id)).field(name)

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------
    def create(self, kind, values=None):
        """Build a record of ``kind`` and return its id."""
        blueprint = self._registry.get(kind)
        supplied = blueprint.accept(values or {})
        record = {}
        for field in blueprint.fields:
            if supplied.get(field.name) is not None:
                record[field.name] = supplied[field.name]
            else:
                record[field.name] = field.default
        blueprint.check_complete(record)
        record_id = self._counters.next_id(kind)
        self._records[record_id] = record
        self._kinds[record_id] = kind
        self._order.append(record_id)
        return record_id

    def create_many(self, kind, rows):
        return [self.create(kind, values) for values in rows]

    def restore(self, record_id, kind, values):
        """Put a record back under an id it already had."""
        if record_id in self._records:
            raise ValidationError(record_id, "is already in use")
        blueprint = self._registry.get(kind)
        record = blueprint.accept(values)
        for field in blueprint.fields:
            if field.name not in record:
                record[field.name] = field.blank()
        blueprint.check_complete(record)
        self._counters.observe(record_id)
        self._records[record_id] = record
        self._kinds[record_id] = kind
        self._order.append(record_id)
        return record_id

    def update(self, record_id, changes):
        """Write ``changes`` into a record and return the result."""
        record = self._stored(record_id)
        blueprint = self._registry.get(self._kinds[record_id])
        if not changes:
            raise ValidationError(record_id, "an empty change set would do nothing")
        record.update(blueprint.accept(changes))
        blueprint.check_complete(record)
        return copy_record(record)

    def append_to(self, record_id, name, value):
        """Add an item to one of a record's list fields."""
        record = self._stored(record_id)
        mutate.append_to(record, self.field_of(record_id, name), value)
        return copy_record(record)

    def extend_with(self, record_id, name, values):
        record = self._stored(record_id)
        mutate.extend_with(record, self.field_of(record_id, name), list(values))
        return copy_record(record)

    def remove_from(self, record_id, name, value):
        record = self._stored(record_id)
        mutate.remove_from(record, self.field_of(record_id, name), value)
        return copy_record(record)

    def put_in(self, record_id, name, key, value):
        """Write one key of a record's map field."""
        record = self._stored(record_id)
        mutate.put_in(record, self.field_of(record_id, name), key, value)
        return copy_record(record)

    def increment(self, record_id, name, by=1):
        record = self._stored(record_id)
        mutate.increment(record, self.field_of(record_id, name), by)
        return copy_record(record)

    def toggle(self, record_id, name):
        record = self._stored(record_id)
        mutate.toggle(record, self.field_of(record_id, name))
        return copy_record(record)

    def reset_field(self, record_id, name):
        """Put one field back to a fresh copy of its blueprint default."""
        record = self._stored(record_id)
        mutate.reset(record, self.field_of(record_id, name))
        return copy_record(record)

    def delete(self, record_id):
        record = self._records.pop(record_id, None)
        if record is None:
            raise RecordNotFound(record_id)
        self._order.remove(record_id)
        del self._kinds[record_id]
        return record

    def clear(self):
        self._records = {}
        self._kinds = {}
        self._order = []

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------
    def get(self, record_id):
        return copy_record(self._stored(record_id))

    def peek(self, record_id, default=None):
        record = self._records.get(record_id)
        return default if record is None else copy_record(record)

    def value_of(self, record_id, name):
        record = self._stored(record_id)
        if name not in record:
            raise UnknownField(self._kinds[record_id], name)
        return copy_record(record)[name]

    def kind_of(self, record_id):
        if record_id not in self._kinds:
            raise RecordNotFound(record_id)
        return self._kinds[record_id]

    def ids(self, kind=None):
        if kind is None:
            return list(self._order)
        return [rid for rid in self._order if self._kinds[rid] == kind]

    def all(self, kind=None):
        return [copy_record(self._records[rid]) for rid in self.ids(kind)]

    def items(self, kind=None):
        return [(rid, copy_record(self._records[rid])) for rid in self.ids(kind)]

    def rows(self, kind=None, fields=None):
        """Records with their id and kind folded in, optionally projected."""
        out = []
        for record_id in self.ids(kind):
            record = self._records[record_id]
            body = only_fields(record, fields) if fields else copy_record(record)
            body["id"] = record_id
            body["kind"] = self._kinds[record_id]
            out.append(body)
        return out

    def sorted_ids(self):
        """Every id, in kind-then-number order rather than creation order."""
        return sorted(self._order, key=id_sort_key)

    def count(self, kind=None):
        return len(self.ids(kind))

    def _stored(self, record_id):
        record = self._records.get(record_id)
        if record is None:
            raise RecordNotFound(record_id)
        return record

    def __len__(self):
        return len(self._order)

    def __contains__(self, record_id):
        return record_id in self._records

    def __iter__(self):
        return iter(self.all())

    def __repr__(self):
        return "Cabinet(records=%d, kinds=%s)" % (len(self._order), self._registry.names())
