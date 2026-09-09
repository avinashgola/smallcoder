"""In-place operations on a stored record.

Each of these takes the record and the :class:`~blueprint.fields.Field`
it belongs to, so the operation can refuse a field of the wrong type
before it touches anything.  They are the only code that writes into a
stored record; the cabinet calls them on its own copies.
"""

from blueprint.errors import ValidationError


def require_kind(field, kind, operation):
    if field.kind != kind:
        raise ValidationError(field.name, "cannot %s a %s field" % (operation, field.kind))
    return field


def append_to(record, field, value):
    """Add one item to a list field."""
    require_kind(field, "list", "append to")
    record.setdefault(field.name, [])
    record[field.name].append(value)
    return record[field.name]


def extend_with(record, field, values):
    """Add several items to a list field."""
    require_kind(field, "list", "append to")
    record.setdefault(field.name, [])
    record[field.name].extend(values)
    return record[field.name]


def remove_from(record, field, value):
    """Drop the first matching item from a list field."""
    require_kind(field, "list", "remove from")
    held = record.get(field.name) or []
    if value in held:
        held.remove(value)
    record[field.name] = held
    return held


def put_in(record, field, key, value):
    """Write one key of a map field."""
    require_kind(field, "map", "write into")
    if not isinstance(key, str):
        raise ValidationError(field.name, "map keys must be strings")
    record.setdefault(field.name, {})
    record[field.name][key] = value
    return record[field.name]


def increment(record, field, by=1):
    """Add to a number field."""
    require_kind(field, "number", "increment")
    if isinstance(by, bool) or not isinstance(by, (int, float)):
        raise ValidationError(field.name, "can only add a number")
    record[field.name] = (record.get(field.name) or 0) + by
    return record[field.name]


def toggle(record, field):
    """Flip a flag field."""
    require_kind(field, "flag", "toggle")
    record[field.name] = not record.get(field.name)
    return record[field.name]


def reset(record, field):
    """Put a field back to a fresh copy of its default."""
    record[field.name] = field.blank()
    return record[field.name]
