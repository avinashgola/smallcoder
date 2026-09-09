"""Reading a snapshot back into a store."""

import json

from catalog.errors import SchemaError
from catalog.store import Store

from .encode import FORMAT_VERSION
from .values import decode_record


def load(payload, store=None):
    """Fill ``store`` (or a fresh one) from a snapshot."""
    if not isinstance(payload, dict):
        raise SchemaError("a snapshot must be a mapping")
    version = payload.get("version")
    if version != FORMAT_VERSION:
        raise SchemaError("unsupported snapshot version %r" % (version,))
    if store is None:
        store = Store()
    restore_indexes(store, payload.get("indexes", ()))
    for entry in payload.get("records", ()):
        if "id" not in entry or "fields" not in entry:
            raise SchemaError("snapshot record is missing 'id' or 'fields'")
        store.insert(decode_record(entry["fields"]), record_id=entry["id"])
    return store


def restore_indexes(store, definitions):
    """Recreate index definitions that the store does not already have."""
    existing = set(store.indexed_fields())
    for definition in definitions:
        field = definition["field"]
        if field in existing:
            continue
        store.add_index(
            field,
            unique=bool(definition.get("unique")),
            multi=bool(definition.get("multi")),
        )


def loads(text, store=None):
    """Fill a store from JSON snapshot text."""
    return load(json.loads(text), store)
