"""The rows a query found, plus the small operations that follow one."""


class RowSet:
    """An ordered set of row ids, resolved against their table on demand."""

    def __init__(self, table, row_ids):
        self.table = table
        self._ids = list(row_ids)

    def ids(self):
        return list(self._ids)

    def rows(self):
        return self.table.rows_by_id(self._ids)

    def column(self, name):
        """The value of ``name`` in every row of the result."""
        return [row.get(name) for row in self.rows()]

    def order_by(self, column, descending=False):
        """Sort by ``column``; empty cells sort last in either direction."""
        rows = list(zip(self._ids, self.rows()))
        rows.sort(key=lambda pair: _sort_key(pair[1].get(column)), reverse=descending)
        return RowSet(self.table, [row_id for row_id, _ in rows])

    def limit(self, count):
        if count < 0:
            raise ValueError("limit must not be negative")
        return RowSet(self.table, self._ids[:count])

    def offset(self, count):
        if count < 0:
            raise ValueError("offset must not be negative")
        return RowSet(self.table, self._ids[count:])

    def first(self):
        rows = self.rows()
        return rows[0] if rows else None

    def is_empty(self):
        return not self._ids

    def __len__(self):
        return len(self._ids)

    def __iter__(self):
        return iter(self.rows())

    def __repr__(self):
        return "RowSet(%r, %d row(s))" % (self.table.name, len(self._ids))


def _sort_key(value):
    """Sort empty cells after everything else, in either direction."""
    if value is None:
        return (1, 0.0, "")
    if isinstance(value, bool):
        return (0, float(value), "")
    if isinstance(value, (int, float)):
        return (0, float(value), "")
    return (0, 0.0, str(value))
