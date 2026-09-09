"""Exceptions raised by the depot."""


class DepotError(Exception):
    """Base class for everything this library raises."""


class EntryNotFound(DepotError):
    """No entry is stored under the requested id."""

    def __init__(self, entry_id):
        super().__init__("no entry with id %r" % (entry_id,))
        self.entry_id = entry_id


class FieldError(DepotError):
    """A field name or value is not something an entry can hold."""


class TagError(DepotError):
    """A tag is empty, malformed or unknown."""


class ArchiveError(DepotError):
    """An archive could not be written or read."""
