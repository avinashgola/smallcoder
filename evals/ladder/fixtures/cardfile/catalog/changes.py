"""Validation of the change sets accepted by :meth:`Store.update`."""

from .errors import SchemaError
from .records import copy_value, normalize_field

DELETE = "__delete__"


def normalize_changes(changes):
    """Return a validated, copied change set.

    A change set maps field names to their new values.  Field removal is
    not supported yet; :data:`DELETE` exists only so a caller that tries
    gets a clear error instead of silently storing the sentinel string.
    """
    if not isinstance(changes, dict):
        raise SchemaError("changes must be a mapping, got %s" % (type(changes).__name__,))
    if not changes:
        raise SchemaError("an empty change set would do nothing")
    patch = {}
    for name, value in changes.items():
        field = normalize_field(name)
        if isinstance(value, str) and value == DELETE:
            raise SchemaError("field removal is not supported")
        patch[field] = copy_value(value)
    return patch


def touched_fields(changes):
    """The canonical names of the fields a change set writes to."""
    return sorted(normalize_field(name) for name in changes)


def is_noop(record, changes):
    """True when applying ``changes`` would leave ``record`` unchanged."""
    for name, value in normalize_changes(changes).items():
        if record.get(name) != value:
            return False
    return True


def apply_changes(record, changes):
    """Return a copy of ``record`` with ``changes`` applied."""
    updated = dict(record)
    updated.update(normalize_changes(changes))
    return updated
