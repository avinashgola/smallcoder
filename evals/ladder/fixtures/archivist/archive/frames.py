"""The value layer of the archive format.

Entries may hold nested lists and dictionaries.  Everything that JSON
can carry travels as itself; a dictionary whose keys are not strings
cannot be written, and is rejected here rather than at ``json.dumps``
time where the error would name no field.
"""

from depot.errors import ArchiveError

JSON_SCALARS = (str, int, float, bool)


def encode_value(value):
    """Return a JSON-safe rendering of one field value."""
    if value is None or isinstance(value, JSON_SCALARS):
        return value
    if isinstance(value, list):
        return [encode_value(item) for item in value]
    if isinstance(value, tuple):
        return [encode_value(item) for item in value]
    if isinstance(value, dict):
        encoded = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ArchiveError("archive keys must be strings, got %r" % (key,))
            encoded[key] = encode_value(item)
        return encoded
    raise ArchiveError("cannot archive a value of type %s" % (type(value).__name__,))


def decode_value(value):
    """Undo :func:`encode_value`."""
    if isinstance(value, list):
        return [decode_value(item) for item in value]
    if isinstance(value, dict):
        return {key: decode_value(item) for key, item in value.items()}
    return value


def frame_keys():
    """The keys every entry frame carries, in their canonical order."""
    return ("id", "revision", "tags", "fields")


def check_frame(frame):
    """Complain about an entry frame that is missing something."""
    if not isinstance(frame, dict):
        raise ArchiveError("entry frames must be mappings")
    for key in frame_keys():
        if key not in frame:
            raise ArchiveError("entry frame is missing %r" % (key,))
    if not isinstance(frame["fields"], dict):
        raise ArchiveError("the fields of an entry frame must be a mapping")
    if not isinstance(frame["tags"], list):
        raise ArchiveError("the tags of an entry frame must be a list")
    return frame
