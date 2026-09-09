"""The row type flowing through the pipeline."""

from common.errors import MissingField


class Record:
    """An immutable mapping of field name to value."""

    __slots__ = ("_fields",)

    def __init__(self, fields=None):
        self._fields = dict(fields or {})

    # -- reading ---------------------------------------------------------

    def get(self, name, default=None):
        return self._fields.get(name, default)

    def require(self, name, stage="?"):
        if name not in self._fields:
            raise MissingField(stage, name)
        return self._fields[name]

    def keys(self):
        return list(self._fields)

    def items(self):
        return list(self._fields.items())

    def as_dict(self):
        return dict(self._fields)

    def __getitem__(self, name):
        return self._fields[name]

    def __contains__(self, name):
        return name in self._fields

    def __len__(self):
        return len(self._fields)

    # -- deriving new records --------------------------------------------

    def with_field(self, name, value):
        fields = dict(self._fields)
        fields[name] = value
        return Record(fields)

    def with_fields(self, **values):
        fields = dict(self._fields)
        fields.update(values)
        return Record(fields)

    def without(self, *names):
        drop = set(names)
        return Record({k: v for k, v in self._fields.items() if k not in drop})

    def renamed(self, mapping):
        return Record({mapping.get(k, k): v for k, v in self._fields.items()})

    # -- plumbing --------------------------------------------------------

    def __eq__(self, other):
        if isinstance(other, Record):
            return self._fields == other._fields
        if isinstance(other, dict):
            return self._fields == other
        return NotImplemented

    def __repr__(self):
        inner = ", ".join("%s=%r" % item for item in sorted(self._fields.items()))
        return "Record(%s)" % inner


def records_from(rows):
    """Build records from a list of dictionaries."""
    return [row if isinstance(row, Record) else Record(row) for row in rows]


def to_dicts(records):
    return [record.as_dict() for record in records]


def field_values(records, name, default=None):
    return [record.get(name, default) for record in records]
