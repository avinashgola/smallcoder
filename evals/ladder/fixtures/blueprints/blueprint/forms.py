"""A blueprint: a named, ordered list of field declarations."""

from .errors import BlueprintError, FieldError, UnknownField
from .fields import Field, check_name


class Blueprint:
    """The declared shape of one kind of record."""

    def __init__(self, name, fields):
        self.name = check_name(name)
        self.fields = []
        self._by_name = {}
        for field in fields:
            self.add(field)
        if not self.fields:
            raise BlueprintError("blueprint %r declares no fields" % (self.name,))

    def add(self, field):
        if not isinstance(field, Field):
            raise FieldError("expected a Field, got %r" % (field,))
        if field.name in self._by_name:
            raise FieldError("field %r is declared twice" % (field.name,))
        self.fields.append(field)
        self._by_name[field.name] = field
        return field

    def field(self, name):
        try:
            return self._by_name[check_name(name)]
        except KeyError:
            raise UnknownField(self.name, name)

    def has(self, name):
        return check_name(name) in self._by_name

    def names(self):
        return [field.name for field in self.fields]

    def required_names(self):
        return [field.name for field in self.fields if field.required]

    def containers(self):
        """The fields whose values are mutable containers."""
        return [field for field in self.fields if field.kind in ("list", "map")]

    def accept(self, values):
        """Cast and check a whole set of supplied values."""
        unknown = set(values) - set(self._by_name)
        if unknown:
            raise UnknownField(self.name, sorted(unknown)[0])
        accepted = {}
        for name, value in values.items():
            accepted[name] = self.field(name).accept(value)
        return accepted

    def check_complete(self, record):
        """Raise unless ``record`` satisfies every required field."""
        for field in self.fields:
            field.check(record.get(field.name))
        return record

    def describe(self):
        return {"name": self.name, "fields": [field.describe() for field in self.fields]}

    @classmethod
    def from_description(cls, described):
        if not isinstance(described, dict):
            raise BlueprintError("a blueprint description must be a mapping")
        fields = [Field.from_description(item) for item in described.get("fields", ())]
        return cls(described["name"], fields)

    def __len__(self):
        return len(self.fields)

    def __iter__(self):
        return iter(self.fields)

    def __repr__(self):
        return "Blueprint(%r, %r)" % (self.name, self.names())
