"""Writing a store out as a snapshot."""

import json

from .values import encode_record

FORMAT_VERSION = 1


def dump(store):
    """Return the snapshot of ``store`` as plain Python data."""
    return {
        "version": FORMAT_VERSION,
        "indexes": index_definitions(store),
        "records": [
            {"id": record_id, "fields": encode_record(record)}
            for record_id, record in store.items()
        ],
    }


def index_definitions(store):
    """Describe the store's indexes well enough to rebuild them."""
    return store.describe_indexes()


def dumps(store, indent=2):
    """Return the snapshot of ``store`` as JSON text."""
    return json.dumps(dump(store), indent=indent, sort_keys=True)


def snapshot_summary(payload):
    """A one-line description of a snapshot, for logs and error messages."""
    records = payload.get("records", [])
    indexes = payload.get("indexes", [])
    return "version %s, %d record(s), %d index(es)" % (
        payload.get("version", "?"),
        len(records),
        len(indexes),
    )
