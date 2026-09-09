"""Indexes over a table's columns.

Two kinds exist.  :class:`~sheets.indexes.lookup_index.LookupIndex`
answers "which rows hold exactly this value"; it is a plain dictionary of
buckets.  :class:`~sheets.indexes.sorted_index.SortedIndex` keeps its
keys in order as well, so a range of values can be answered without
touching every row.  :class:`~sheets.indexes.manager.IndexSet` owns the
indexes belonging to one table and fans every write out to them.
"""

from .lookup_index import LookupIndex
from .manager import IndexSet
from .sorted_index import SortedIndex

__all__ = ["LookupIndex", "SortedIndex", "IndexSet"]
