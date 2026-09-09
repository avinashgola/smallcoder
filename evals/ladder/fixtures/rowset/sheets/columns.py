"""Column declarations and the set of them that makes up a table."""

from .coerce import KINDS, coerce, is_comparable
from .errors import ColumnError


class Column:
    """One declared column: a name, a type and whether it may be empty."""

    def __init__(self, name, kind="text", required=False):
        if not isinstance(name, str) or not name.strip():
            raise ColumnError("column names must be non-empty strings")
        if kind not in KINDS:
            raise ColumnError("unknown column type %r for %r" % (kind, name))
        self.name = name.strip().lower()
        self.kind = kind
        self.required = bool(required)

    @property
    def orderable(self):
        return is_comparable(self.kind)

    def cast(self, value):
        """Coerce ``value`` for storage in this column."""
        casted = coerce(self.name, value, self.kind)
        if casted is None and self.required:
            raise ColumnError("column %r is required" % (self.name,))
        return casted

    def __repr__(self):
        return "Column(%r, %r%s)" % (
            self.name,
            self.kind,
            ", required=True" if self.required else "",
        )


class ColumnSet:
    """The ordered collection of columns belonging to one table."""

    def __init__(self, columns):
        self._columns = {}
        self._order = []
        for column in columns:
            self.add(column)

    def add(self, column):
        if not isinstance(column, Column):
            raise ColumnError("expected a Column, got %r" % (column,))
        if column.name in self._columns:
            raise ColumnError("column %r is declared twice" % (column.name,))
        self._columns[column.name] = column
        self._order.append(column.name)
        return column

    def get(self, name):
        try:
            return self._columns[name]
        except KeyError:
            raise ColumnError("unknown column %r" % (name,))

    def has(self, name):
        return name in self._columns

    def names(self):
        return list(self._order)

    def kinds(self):
        return {name: self._columns[name].kind for name in self._order}

    def cast_row(self, values):
        """Coerce a whole row, filling absent columns with ``None``."""
        unknown = set(values) - set(self._columns)
        if unknown:
            raise ColumnError("unknown column(s): %s" % (", ".join(sorted(unknown)),))
        row = {}
        for name in self._order:
            column = self._columns[name]
            row[name] = column.cast(values.get(name))
        return row

    def cast_changes(self, changes):
        """Coerce a partial row, leaving untouched columns out."""
        casted = {}
        for name, value in changes.items():
            casted[name] = self.get(name).cast(value)
        return casted

    def __len__(self):
        return len(self._order)

    def __iter__(self):
        return iter(self._columns[name] for name in self._order)

    def __repr__(self):
        return "ColumnSet(%r)" % (self._order,)
