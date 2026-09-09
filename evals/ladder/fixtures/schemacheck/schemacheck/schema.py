"""A named group of fields, and checking a payload against it."""

from .errors import ValidationError


class Schema:
    """The declared shape of one payload."""

    def __init__(self, name, fields):
        self.name = name
        self.fields = tuple(fields)

    def __iter__(self):
        return iter(self.fields)

    def names(self):
        return [field.name for field in self.fields]

    def field(self, name):
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)

    def errors_for(self, payload):
        return collect_errors(payload, self)

    def is_valid(self, payload):
        return not collect_errors(payload, self)

    def validate(self, payload):
        """Return the payload, or raise with every problem at once."""
        errors = collect_errors(payload, self)
        if errors:
            raise ValidationError(self.name, errors)
        return payload

    def __repr__(self):
        return f"Schema({self.name!r}, {len(self.fields)} fields)"


def collect_errors(payload, schema):
    """Every problem with ``payload``: one message per offending field.

    Declared fields are checked in the order the schema lists them, and any
    field the schema does not declare is reported afterwards.
    """
    errors = []
    for field in schema:
        if field.name not in payload:
            if field.required:
                errors.append(f"{field.name}: this field is required")
            continue
        problem = field.check(payload[field.name])
        if problem is None:
            return errors
        errors.append(f"{field.name}: {problem}")
    for name in sorted(set(payload) - set(schema.names())):
        errors.append(f"{name}: unknown field")
    return errors
