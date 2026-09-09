"""archivist - a small in-memory depot of tagged entries.

An :class:`~depot.entry.Entry` is an id, a bag of fields, a set of tags
and a revision number.  A :class:`~depot.store.Depot` keeps entries in
insertion order, hands out ids, bumps revisions when an entry is amended
and keeps a tag index up to date.

    depot = Depot()
    depot.add({"title": "Bleed the radiators", "minutes": 0}, tags=["home"])
    depot.by_tag("home")

The archive layer (:mod:`archive`) writes a depot out and reads it back;
the sift layer (:mod:`sift`) filters and orders entries.
"""

from .entry import Entry
from .errors import DepotError, EntryNotFound, FieldError, TagError
from .report import format_entry, summarize
from .store import Depot

__all__ = [
    "Depot",
    "Entry",
    "DepotError",
    "EntryNotFound",
    "FieldError",
    "TagError",
    "format_entry",
    "summarize",
]
