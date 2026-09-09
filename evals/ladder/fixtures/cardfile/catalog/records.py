"""Helpers for the plain dictionaries the catalogue stores.

A record maps lower-case field names to JSON-friendly values.  Nothing
here subclasses ``dict``: keeping records as plain mappings makes them
trivial to snapshot, compare and print in tests.
"""

from .errors import SchemaError

RESERVED_FIELDS = frozenset({"id"})


def normalize_field(name):
    """Return the canonical spelling of one field name."""
    if not isinstance(name, str):
        raise SchemaError("field names must be strings, got %r" % (name,))
    cleaned = name.strip().lower()
    if not cleaned:
        raise SchemaError("field names must not be blank")
    return cleaned


def normalize_record(values):
    """Return a new record with canonical field names and copied values."""
    if not isinstance(values, dict):
        raise SchemaError("records must be mappings, got %s" % (type(values).__name__,))
    record = {}
    for name, value in values.items():
        field = normalize_field(name)
        if field in RESERVED_FIELDS:
            raise SchemaError("%r is reserved and cannot be stored" % (field,))
        record[field] = copy_value(value)
    return record


def copy_value(value):
    """Copy the containers the catalogue understands, share everything else."""
    if isinstance(value, dict):
        return {key: copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_value(item) for item in value]
    return value


def copy_record(record):
    """Return a detached copy of ``record``."""
    return {name: copy_value(value) for name, value in record.items()}


def project(record, fields):
    """Return only ``fields`` from ``record``, skipping the ones it lacks."""
    wanted = [normalize_field(name) for name in fields]
    return {name: copy_value(record[name]) for name in wanted if name in record}


def merge(record, other):
    """Return ``record`` overlaid with the fields of ``other``."""
    merged = copy_record(record)
    merged.update(normalize_record(other))
    return merged


def diff(before, after):
    """Fields that differ between two records, as ``name -> (old, new)``."""
    changed = {}
    for name in sorted(set(before) | set(after)):
        old = before.get(name)
        new = after.get(name)
        if old != new:
            changed[name] = (old, new)
    return changed


def field_names(records):
    """Every field name used across ``records``, in sorted order."""
    names = set()
    for record in records:
        names.update(record)
    return sorted(names)


def pluck(records, field, default=None):
    """The value of ``field`` from each record."""
    return [record.get(field, default) for record in records]
