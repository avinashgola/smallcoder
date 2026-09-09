"""An ordered index: the keys of one column, kept in sorted order.

The index holds two structures side by side: ``_keys`` is the sorted list
of distinct keys and ``_buckets`` maps each key to the row ids that carry
it.  Bisecting ``_keys`` turns a range question into two binary searches
instead of a walk over every row.

Rows whose value is ``None`` are not filed at all: ``None`` does not
order against numbers or text, and no range can contain it.
"""

import bisect


class SortedIndex:
    """Answers equality and range questions about one orderable column."""

    ordered = True

    def __init__(self, column):
        self.column = column
        self._keys = []
        self._buckets = {}

    # -- maintenance ---------------------------------------------------
    def add(self, row_id, row):
        key = row.get(self.column)
        if key is None:
            return
        bucket = self._buckets.get(key)
        if bucket is None:
            self._buckets[key] = {row_id}
            bisect.insort(self._keys, key)
        else:
            bucket.add(row_id)

    def remove(self, row_id, row):
        key = row.get(self.column)
        if key is None:
            return
        bucket = self._buckets.get(key)
        if bucket is None:
            return
        bucket.discard(row_id)
        if not bucket:
            del self._buckets[key]
            position = bisect.bisect_left(self._keys, key)
            if position < len(self._keys) and self._keys[position] == key:
                del self._keys[position]

    def clear(self):
        self._keys = []
        self._buckets = {}

    # -- questions -----------------------------------------------------
    def ids_for(self, value):
        """Row ids whose key equals ``value``."""
        return sorted(self._buckets.get(value, ()))

    def between(self, low, high):
        """Row ids whose key satisfies ``low <= key <= high``.

        Both bounds are part of the range.
        """
        start = bisect.bisect_left(self._keys, low)
        stop = bisect.bisect_left(self._keys, high)
        return self._ids_in(self._keys[start:stop])

    def at_least(self, low):
        """Row ids whose key satisfies ``low <= key``."""
        start = bisect.bisect_left(self._keys, low)
        return self._ids_in(self._keys[start:])

    def at_most(self, high):
        """Row ids whose key satisfies ``key <= high``."""
        stop = bisect.bisect_right(self._keys, high)
        return self._ids_in(self._keys[:stop])

    def _ids_in(self, keys):
        found = []
        for key in keys:
            found.extend(sorted(self._buckets[key]))
        return found

    def keys(self):
        return list(self._keys)

    def span(self):
        """The lowest and highest keys held, or ``None`` when empty."""
        if not self._keys:
            return None
        return (self._keys[0], self._keys[-1])

    def cardinality(self):
        return len(self._keys)

    def __contains__(self, value):
        return value in self._buckets

    def __len__(self):
        return sum(len(bucket) for bucket in self._buckets.values())

    def __repr__(self):
        return "SortedIndex(%r, keys=%d)" % (self.column, len(self._keys))
