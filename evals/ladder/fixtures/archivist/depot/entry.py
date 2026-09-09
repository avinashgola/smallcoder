"""One stored entry: an id, its fields, its tags and its revision."""

from .errors import FieldError
from .tags.tagset import TagSet

SCALARS = (str, int, float, bool)


def normalize_name(name):
    """Return the canonical spelling of one field name."""
    if not isinstance(name, str):
        raise FieldError("field names must be strings, got %r" % (name,))
    cleaned = name.strip().lower()
    if not cleaned:
        raise FieldError("field names must not be blank")
    return cleaned


def check_value(name, value):
    """Refuse values an archive would not be able to write back out."""
    if value is None or isinstance(value, SCALARS):
        return value
    if isinstance(value, list):
        for item in value:
            check_value(name, item)
        return value
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise FieldError("keys inside %r must be strings" % (name,))
            check_value(name, item)
        return value
    raise FieldError("field %r cannot hold a %s" % (name, type(value).__name__))


def normalize_fields(values):
    """Canonicalise a whole bag of fields, copying containers."""
    if not isinstance(values, dict):
        raise FieldError("fields must be a mapping, got %s" % (type(values).__name__,))
    fields = {}
    for name, value in values.items():
        field = normalize_name(name)
        check_value(field, value)
        fields[field] = copy_value(value)
    return fields


def copy_value(value):
    if isinstance(value, dict):
        return {key: copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_value(item) for item in value]
    return value


class Entry:
    """An entry as the depot hands it out: detached and comparable."""

    def __init__(self, entry_id, fields=None, tags=(), revision=1):
        self.id = entry_id
        self.fields = normalize_fields(fields) if fields else {}
        self.tags = tags if isinstance(tags, TagSet) else TagSet(tags)
        self.revision = revision

    def get(self, name, default=None):
        return self.fields.get(normalize_name(name), default)

    def has(self, name):
        return normalize_name(name) in self.fields

    def names(self):
        return sorted(self.fields)

    def with_fields(self, changes):
        """A copy of this entry with ``changes`` written into it."""
        merged = dict(self.fields)
        merged.update(normalize_fields(changes))
        return Entry(self.id, merged, self.tags.copy(), self.revision)

    def copy(self):
        return Entry(self.id, self.fields, self.tags.copy(), self.revision)

    def as_dict(self):
        """A plain-dictionary view, handy in tests and error messages."""
        return {
            "id": self.id,
            "revision": self.revision,
            "tags": self.tags.as_list(),
            "fields": copy_value(self.fields),
        }

    def __eq__(self, other):
        if not isinstance(other, Entry):
            return NotImplemented
        return (
            self.id == other.id
            and self.revision == other.revision
            and self.fields == other.fields
            and self.tags == other.tags
        )

    __hash__ = None

    def __repr__(self):
        return "Entry(%r, rev=%d, tags=%r, fields=%r)" % (
            self.id,
            self.revision,
            self.tags.as_list(),
            self.fields,
        )
