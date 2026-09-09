"""Reading a cabinet back."""

import json

from blueprint.errors import BlueprintError
from blueprint.forms import Blueprint
from blueprint.registry import Registry
from cabinet.drawer import Cabinet

from .write import FORMAT_VERSION


def read_registry(descriptions):
    """Rebuild the blueprints of a saved cabinet."""
    registry = Registry()
    for description in descriptions:
        registry.register(Blueprint.from_description(description))
    return registry


def load(payload):
    """Rebuild a whole cabinet from saved data."""
    if not isinstance(payload, dict):
        raise BlueprintError("saved cabinets are mappings")
    version = payload.get("version")
    if version != FORMAT_VERSION:
        raise BlueprintError("unsupported save version %r" % (version,))
    cabinet = Cabinet(read_registry(payload.get("blueprints", ())))
    for entry in payload.get("records", ()):
        for key in ("id", "kind", "fields"):
            if key not in entry:
                raise BlueprintError("saved record is missing %r" % (key,))
        cabinet.restore(entry["id"], entry["kind"], entry["fields"])
    return cabinet


def loads(text):
    """Rebuild a cabinet from JSON text."""
    try:
        payload = json.loads(text)
    except ValueError:
        raise BlueprintError("saved cabinet is not valid JSON")
    return load(payload)
