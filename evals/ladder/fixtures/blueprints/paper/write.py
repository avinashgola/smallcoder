"""Writing a cabinet out."""

import json

from cabinet.values import copy_record

FORMAT_VERSION = 1


def dump(cabinet):
    """Return the whole cabinet as plain, JSON-safe data."""
    return {
        "version": FORMAT_VERSION,
        "blueprints": [cabinet.blueprint(kind).describe() for kind in cabinet.kinds()],
        "records": [
            {"id": record_id, "kind": cabinet.kind_of(record_id), "fields": copy_record(record)}
            for record_id, record in cabinet.items()
        ],
    }


def dumps(cabinet, indent=2):
    """Return the whole cabinet as JSON text."""
    return json.dumps(dump(cabinet), indent=indent, sort_keys=True)


def summary(payload):
    """A one-line description of saved data, for logs and errors."""
    return "version %s, %d blueprint(s), %d record(s)" % (
        payload.get("version", "?"),
        len(payload.get("blueprints", ())),
        len(payload.get("records", ())),
    )
