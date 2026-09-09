"""Value coding for snapshots.

JSON has no tuples and no sets, and a catalogue is allowed to hold both.
Values of those types are wrapped in a small tagged object on the way
out and unwrapped on the way back in; everything else travels as itself.
"""

from catalog.errors import SchemaError

TYPE_TAG = "$type"
VALUE_KEY = "items"
JSON_SCALARS = (str, int, float, bool)


def encode_value(value):
    """Return a JSON-safe rendering of ``value``."""
    if value is None or isinstance(value, JSON_SCALARS):
        return value
    if isinstance(value, list):
        return [encode_value(item) for item in value]
    if isinstance(value, tuple):
        return {TYPE_TAG: "tuple", VALUE_KEY: [encode_value(item) for item in value]}
    if isinstance(value, set):
        items = sorted(value, key=lambda item: (type(item).__name__, repr(item)))
        return {TYPE_TAG: "set", VALUE_KEY: [encode_value(item) for item in items]}
    if isinstance(value, dict):
        if TYPE_TAG in value:
            raise SchemaError("records may not use the reserved key %r" % (TYPE_TAG,))
        return {key: encode_value(item) for key, item in value.items()}
    raise SchemaError("cannot encode a value of type %s" % (type(value).__name__,))


def decode_value(value):
    """Undo :func:`encode_value`."""
    if isinstance(value, list):
        return [decode_value(item) for item in value]
    if isinstance(value, dict):
        tag = value.get(TYPE_TAG)
        if tag == "tuple":
            return tuple(decode_value(item) for item in value[VALUE_KEY])
        if tag == "set":
            return set(decode_value(item) for item in value[VALUE_KEY])
        if tag is not None:
            raise SchemaError("unknown value tag %r" % (tag,))
        return {key: decode_value(item) for key, item in value.items()}
    return value


def encode_record(record):
    return {name: encode_value(record[name]) for name in sorted(record)}


def decode_record(payload):
    if not isinstance(payload, dict):
        raise SchemaError("records in a snapshot must be mappings")
    return {name: decode_value(value) for name, value in payload.items()}
