"""Field declarations: the type, the default and the checks."""

from .defaults import blank_for, clone_default, is_container_kind, kind_of
from .errors import FieldError, ValidationError

UNSET = object()
MAX_NAME_LENGTH = 40


class Field:
    """One declared field of a blueprint.

    ``kind`` is one of ``text``, ``number``, ``flag``, ``list`` or
    ``map``.  ``default`` is what a record gets when the field is not
    supplied; leaving it out uses the blank value for the type.  A field
    may also carry ``choices``, a list of the values it will accept.
    """

    def __init__(self, name, kind="text", required=False, default=UNSET, choices=None):
        self.name = check_name(name)
        if kind not in ("text", "number", "flag", "list", "map"):
            raise FieldError("unknown field type %r for %r" % (kind, name))
        self.kind = kind
        self.required = bool(required)
        self.choices = list(choices) if choices else None
        if self.choices is not None:
            if is_container_kind(kind):
                raise FieldError("a %s field cannot have choices" % (kind,))
            for choice in self.choices:
                if kind_of(choice) != kind:
                    raise FieldError("choice %r does not fit a %s field" % (choice, kind))
        self.default = blank_for(kind) if default is UNSET else self.cast(default)

    def blank(self):
        """A fresh copy of this field's default.

        Container defaults are copied rather than shared, so a caller can
        keep whatever it is given without reaching back into the field.
        """
        return clone_default(self.default)

    def cast(self, value):
        """Coerce ``value`` into this field's type where that is safe."""
        if value is None:
            return None
        if self.kind == "number" and isinstance(value, bool):
            raise ValidationError(self.name, "a flag is not a number")
        if self.kind == "number" and isinstance(value, str):
            return parse_number(self.name, value)
        if self.kind == "text" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        if self.kind == "list" and isinstance(value, tuple):
            return list(value)
        return value

    def check(self, value):
        """Raise unless ``value`` is acceptable for this field."""
        if value is None:
            if self.required:
                raise ValidationError(self.name, "is required")
            return None
        found = kind_of(value)
        if found != self.kind:
            raise ValidationError(
                self.name, "expected %s, got %s" % (self.kind, found or "something else")
            )
        if self.choices is not None and value not in self.choices:
            raise ValidationError(self.name, "%r is not one of %r" % (value, self.choices))
        if self.required and value == blank_for(self.kind):
            raise ValidationError(self.name, "is required")
        return value

    def accept(self, value):
        """Cast, check, and return a value a record can keep.

        The result is detached from whatever the caller passed in, so a
        list handed to a record cannot go on being changed from outside.
        """
        return clone_default(self.check(self.cast(value)))

    def describe(self):
        """The declaration as plain data, for writing a blueprint out."""
        described = {
            "name": self.name,
            "kind": self.kind,
            "required": self.required,
            "default": clone_default(self.default),
        }
        if self.choices is not None:
            described["choices"] = list(self.choices)
        return described

    @classmethod
    def from_description(cls, described):
        """Rebuild a field from :meth:`describe` output."""
        if not isinstance(described, dict) or "name" not in described:
            raise FieldError("a field description needs at least a name")
        return cls(
            described["name"],
            described.get("kind", "text"),
            required=described.get("required", False),
            default=described.get("default", UNSET),
            choices=described.get("choices"),
        )

    def __eq__(self, other):
        if not isinstance(other, Field):
            return NotImplemented
        return self.describe() == other.describe()

    __hash__ = None

    def __repr__(self):
        return "Field(%r, %r%s)" % (
            self.name,
            self.kind,
            ", required=True" if self.required else "",
        )


def check_name(name):
    """Return the canonical spelling of a field name."""
    if not isinstance(name, str):
        raise FieldError("field names must be strings, got %r" % (name,))
    cleaned = name.strip().lower()
    if not cleaned:
        raise FieldError("field names must not be blank")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise FieldError("field name %r is too long" % (name,))
    if any(character.isspace() for character in cleaned):
        raise FieldError("field names may not contain spaces: %r" % (name,))
    return cleaned


def parse_number(name, text):
    """Read a number written as text, refusing anything ambiguous."""
    body = text.strip()
    try:
        return int(body)
    except ValueError:
        pass
    try:
        return float(body)
    except ValueError:
        raise ValidationError(name, "%r is not a number" % (text,))
