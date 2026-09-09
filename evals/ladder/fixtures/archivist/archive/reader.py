"""Reading an archive back into a depot."""

import json

from depot.entry import Entry
from depot.errors import ArchiveError
from depot.store import Depot
from depot.tags.tagset import TagSet

from .frames import check_frame, decode_value
from .manifest import check_manifest


def decode_entry(frame):
    """Rebuild one entry from its frame.

    A field the frame does not carry is a field the entry does not have;
    nothing is invented to fill the gap.
    """
    check_frame(frame)
    fields = {name: decode_value(value) for name, value in frame["fields"].items()}
    revision = frame["revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ArchiveError("bad revision %r" % (revision,))
    return Entry(frame["id"], fields, TagSet(frame["tags"]), revision)


def load(payload, depot=None):
    """Fill ``depot`` (or a fresh one) from an archive."""
    if not isinstance(payload, dict):
        raise ArchiveError("an archive must be a mapping")
    frames = payload.get("entries")
    if not isinstance(frames, list):
        raise ArchiveError("an archive must carry a list of entries")
    check_manifest(payload.get("manifest"), frames)
    if depot is None:
        depot = Depot()
    for frame in frames:
        depot.restore(decode_entry(frame))
    return depot


def loads(text, depot=None):
    """Fill a depot from archive text."""
    try:
        payload = json.loads(text)
    except ValueError:
        raise ArchiveError("archive text is not valid JSON")
    return load(payload, depot)
