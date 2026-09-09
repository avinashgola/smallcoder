"""Exceptions raised by the table layer."""


class TableError(Exception):
    """Base class for everything this library raises."""


class ColumnError(TableError):
    """A column is unknown, duplicated or declared with a bad type."""


class RowNotFound(TableError):
    """No row is stored under the requested id."""

    def __init__(self, row_id):
        super().__init__("no row with id %r" % (row_id,))
        self.row_id = row_id


class ValueError_(TableError):
    """A value could not be coerced to its column's declared type.

    Named with a trailing underscore so it does not shadow the builtin;
    it is exported as ``CoercionError``.
    """

    def __init__(self, column, value, kind):
        super().__init__("cannot store %r in %r (declared %s)" % (value, column, kind))
        self.column = column
        self.value = value
        self.kind = kind


class IndexError_(TableError):
    """An index was asked for something it cannot answer."""
