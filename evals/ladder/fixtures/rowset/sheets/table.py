"""The table itself: typed columns, integer row ids and indexes.

Rows are stored as plain dictionaries keyed by every declared column, so
a row always has the same shape whether or not the caller supplied every
value.  Row ids are integers handed out in order; they are never reused,
which means an id in a saved query result never silently points at a
different row later on.

Reads hand back copies.  An index can only stay in step with the rows if
nothing mutates a stored row behind the table's back.
"""

from .columns import Column, ColumnSet
from .errors import ColumnError, RowNotFound, TableError
from .indexes.manager import IndexSet


class Table:
    """An ordered collection of rows with declared columns."""

    def __init__(self, name, columns):
        self.name = name
        self.columns = columns if isinstance(columns, ColumnSet) else ColumnSet(columns)
        self._rows = {}
        self._order = []
        self._next_id = 1
        self._indexes = IndexSet()

    # ------------------------------------------------------------------
    # structure
    # ------------------------------------------------------------------
    def column_names(self):
        return self.columns.names()

    def add_index(self, column, ordered=False):
        """Define an index and backfill it from the rows already stored.

        An ordered index needs comparable keys, so it is refused on
        boolean columns.
        """
        declared = self.columns.get(column)
        if ordered and not declared.orderable:
            raise ColumnError("column %r cannot carry an ordered index" % (column,))
        index = self._indexes.add(column, ordered=ordered)
        for row_id in self._order:
            index.add(row_id, self._rows[row_id])
        return index

    def drop_index(self, column):
        self._indexes.drop(column)

    def indexed_columns(self):
        return self._indexes.columns()

    def ordered_index(self, column):
        """The ordered index on ``column``, or ``None``."""
        return self._indexes.ordered_for(column)

    def lookup_index(self, column):
        """An index able to answer equality on ``column``, or ``None``."""
        return self._indexes.lookup_for(column)

    def rebuild_indexes(self):
        self._indexes.rebuild((row_id, self._rows[row_id]) for row_id in self._order)

    def index_summary(self):
        return self._indexes.summary()

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------
    def add_row(self, values):
        """Store one row and return its id."""
        row = self.columns.cast_row(values)
        row_id = self._next_id
        self._next_id += 1
        self._rows[row_id] = row
        self._order.append(row_id)
        self._indexes.insert(row_id, row)
        return row_id

    def add_rows(self, rows):
        return [self.add_row(values) for values in rows]

    def restore_row(self, row_id, values):
        """Store a row under an id it already had, as a reload does.

        Ids stay unique afterwards: the next generated id is pushed past
        anything restored here.
        """
        if not isinstance(row_id, int) or isinstance(row_id, bool) or row_id < 1:
            raise TableError("row ids are positive integers, got %r" % (row_id,))
        if row_id in self._rows:
            raise TableError("row id %r is already in use" % (row_id,))
        row = self.columns.cast_row(values)
        self._rows[row_id] = row
        self._order.append(row_id)
        self._next_id = max(self._next_id, row_id + 1)
        self._indexes.insert(row_id, row)
        return row_id

    def update_row(self, row_id, changes):
        """Write ``changes`` into an existing row and refile it."""
        current = self._rows.get(row_id)
        if current is None:
            raise RowNotFound(row_id)
        if not changes:
            raise ColumnError("an empty change set would do nothing")
        previous = dict(current)
        current.update(self.columns.cast_changes(changes))
        self._indexes.replace(row_id, previous, current)
        return dict(current)

    def delete_row(self, row_id):
        row = self._rows.pop(row_id, None)
        if row is None:
            raise RowNotFound(row_id)
        self._order.remove(row_id)
        self._indexes.remove(row_id, row)
        return row

    def clear(self):
        self._rows = {}
        self._order = []
        self._indexes.clear()

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------
    def row(self, row_id):
        row = self._rows.get(row_id)
        if row is None:
            raise RowNotFound(row_id)
        return dict(row)

    def peek(self, row_id, default=None):
        row = self._rows.get(row_id)
        return default if row is None else dict(row)

    def ids(self):
        return list(self._order)

    def rows(self):
        """Every row, in insertion order."""
        return [dict(self._rows[row_id]) for row_id in self._order]

    def items(self):
        return [(row_id, dict(self._rows[row_id])) for row_id in self._order]

    def rows_by_id(self, row_ids):
        """The named rows, skipping ids that are no longer stored."""
        return [dict(self._rows[row_id]) for row_id in row_ids if row_id in self._rows]

    def in_order(self, row_ids):
        """The given ids sorted into the table's own row order.

        Index lookups come back grouped by key, so anything built from
        one is put back into row order before it reaches a caller.
        """
        position = {row_id: place for place, row_id in enumerate(self._order)}
        known = [row_id for row_id in row_ids if row_id in position]
        return sorted(known, key=lambda row_id: position[row_id])

    def column_values(self, column):
        """The value of ``column`` in every row, in insertion order."""
        self.columns.get(column)
        return [self._rows[row_id][column] for row_id in self._order]

    def distinct(self, column):
        """The distinct values of ``column``, first-seen order."""
        seen = []
        for value in self.column_values(column):
            if value not in seen:
                seen.append(value)
        return seen

    def __len__(self):
        return len(self._order)

    def __contains__(self, row_id):
        return row_id in self._rows

    def __iter__(self):
        return iter(self.rows())

    def __repr__(self):
        return "Table(%r, rows=%d, indexes=%s)" % (
            self.name,
            len(self._order),
            self._indexes.columns(),
        )


def table_from_spec(name, spec):
    """Build a table from ``{"column": "kind"}`` or a list of ``Column``s."""
    if isinstance(spec, dict):
        columns = [Column(column, kind) for column, kind in spec.items()]
    else:
        columns = list(spec)
    return Table(name, columns)
