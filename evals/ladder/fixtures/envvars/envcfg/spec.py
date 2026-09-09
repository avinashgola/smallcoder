"""Declarations: which settings exist and what they look like."""

from .errors import InvalidSetting


class Field:
    """One setting."""

    def __init__(self, name, kind="str", default=None, required=False,
                 secret=False, choices=()):
        self.name = name
        self.kind = kind
        self.default = default
        self.required = required
        self.secret = secret
        self.choices = tuple(choices)

    def __repr__(self):
        return f"Field({self.name!r}, kind={self.kind!r})"


class Spec:
    """An ordered group of fields sharing a variable-name prefix."""

    def __init__(self, prefix, fields):
        self.prefix = prefix
        self.fields = tuple(fields)

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def names(self):
        return [field.name for field in self.fields]

    def field(self, name):
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)

    def env_name(self, field):
        """Variable a field is read from: ``Spec("APP_")`` + ``port`` -> APP_PORT."""
        return f"{self.prefix}{field.name.upper()}"

    def check(self, values):
        """Validate an already-loaded mapping against the declared choices."""
        for field in self.fields:
            if not field.choices:
                continue
            value = values.get(field.name)
            if value is None and not field.required:
                continue
            if value not in field.choices:
                raise InvalidSetting(field.name, value, field.choices)
