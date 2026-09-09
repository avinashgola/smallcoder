"""The set of indexes belonging to one table."""

from ..errors import ColumnError, IndexError_
from .lookup_index import LookupIndex
from .sorted_index import SortedIndex


class IndexSet:
    """Fans a table's writes out to every index defined on it."""

    def __init__(self):
        self._indexes = {}

    def add(self, column, ordered=False):
        if column in self._indexes:
            raise IndexError_("column %r is already indexed" % (column,))
        index = SortedIndex(column) if ordered else LookupIndex(column)
        self._indexes[column] = index
        return index

    def drop(self, column):
        self._indexes.pop(column, None)

    def has(self, column):
        return column in self._indexes

    def get(self, column):
        if column not in self._indexes:
            raise ColumnError("no index on column %r" % (column,))
        return self._indexes[column]

    def ordered_for(self, column):
        """The ordered index on ``column``, or ``None`` if there isn't one."""
        index = self._indexes.get(column)
        if index is None or not index.ordered:
            return None
        return index

    def lookup_for(self, column):
        """Any index able to answer an equality question about ``column``."""
        return self._indexes.get(column)

    def columns(self):
        return sorted(self._indexes)

    def insert(self, row_id, row):
        for index in self._indexes.values():
            index.add(row_id, row)

    def remove(self, row_id, row):
        for index in self._indexes.values():
            index.remove(row_id, row)

    def replace(self, row_id, previous, updated):
        """Refile ``row_id`` after its row changed from ``previous`` to ``updated``."""
        self.remove(row_id, previous)
        self.insert(row_id, updated)

    def rebuild(self, rows):
        for index in self._indexes.values():
            index.clear()
        for row_id, row in rows:
            self.insert(row_id, row)

    def clear(self):
        for index in self._indexes.values():
            index.clear()

    def summary(self):
        return {column: index.cardinality() for column, index in self._indexes.items()}

    def __len__(self):
        return len(self._indexes)
