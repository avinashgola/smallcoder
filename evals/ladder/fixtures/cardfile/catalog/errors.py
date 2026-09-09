"""Exceptions raised by the catalogue."""


class CatalogError(Exception):
    """Base class for every error this package raises."""


class RecordNotFound(CatalogError):
    """No record is stored under the requested id."""

    def __init__(self, record_id):
        super().__init__("no record with id %r" % (record_id,))
        self.record_id = record_id


class DuplicateKey(CatalogError):
    """A unique index already holds the key being filed."""

    def __init__(self, field, key):
        super().__init__("unique index on %r already holds key %r" % (field, key))
        self.field = field
        self.key = key


class SchemaError(CatalogError):
    """A record or change set does not have the shape the catalogue expects."""


class QueryError(CatalogError):
    """A query specification could not be understood."""
