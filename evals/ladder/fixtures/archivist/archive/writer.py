"""Writing a depot out as an archive."""

import json

from .frames import encode_value
from .manifest import build_manifest


def encode_entry(entry):
    """Render one entry as the archive stores it.

    Fields that were never filled in are left out of the frame rather
    than written as nulls: the reader puts an absent field back as an
    absent field, so the entry comes home the same shape it left.
    """
    body = {}
    for name in sorted(entry.fields):
        value = entry.fields[name]
        if not value:
            continue
        body[name] = encode_value(value)
    return {
        "id": entry.id,
        "revision": entry.revision,
        "tags": entry.tags.as_list(),
        "fields": body,
    }


def encode_entries(entries):
    return [encode_entry(entry) for entry in entries]


def dump(depot):
    """Return the archive of ``depot`` as plain Python data."""
    frames = encode_entries(depot.entries())
    return {"manifest": build_manifest(frames), "entries": frames}


def dumps(depot, indent=2):
    """Return the archive of ``depot`` as JSON text."""
    return json.dumps(dump(depot), indent=indent, sort_keys=True)
