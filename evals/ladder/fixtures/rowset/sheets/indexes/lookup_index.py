"""An exact-match index: value -> the rows that hold it."""


class LookupIndex:
    """Buckets row ids by the raw value of one column.

    Unlike the ordered index this one is happy to file ``None``: "which
    rows have no owner" is a question worth answering quickly.
    """

    ordered = False

    def __init__(self, column):
        self.column = column
        self._buckets = {}

    def add(self, row_id, row):
        key = row.get(self.column)
        self._buckets.setdefault(key, set()).add(row_id)

    def remove(self, row_id, row):
        key = row.get(self.column)
        bucket = self._buckets.get(key)
        if bucket is None:
            return
        bucket.discard(row_id)
        if not bucket:
            del self._buckets[key]

    def ids_for(self, value):
        """Row ids holding exactly ``value``, lowest id first."""
        return sorted(self._buckets.get(value, ()))

    def ids_for_any(self, values):
        """Row ids holding any of ``values``, without duplicates."""
        found = set()
        for value in values:
            found.update(self._buckets.get(value, ()))
        return sorted(found)

    def values(self):
        """The distinct values held, with ``None`` sorted last."""
        present = [key for key in self._buckets if key is not None]
        present.sort()
        if None in self._buckets:
            present.append(None)
        return present

    def cardinality(self):
        return len(self._buckets)

    def clear(self):
        self._buckets = {}

    def __contains__(self, value):
        return value in self._buckets

    def __len__(self):
        return sum(len(bucket) for bucket in self._buckets.values())

    def __repr__(self):
        return "LookupIndex(%r, values=%d)" % (self.column, len(self._buckets))
