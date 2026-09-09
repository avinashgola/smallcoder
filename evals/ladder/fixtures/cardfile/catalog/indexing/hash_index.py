"""A non-unique secondary index: key -> set of record ids."""

from .keys import keys_for


class HashIndex:
    """Files record ids under every key their indexed field produces."""

    unique = False

    def __init__(self, field, multi=False):
        self.field = field
        self.multi = multi
        self._buckets = {}

    def add(self, record_id, record):
        for key in keys_for(record, self.field, self.multi):
            self._buckets.setdefault(key, set()).add(record_id)

    def remove(self, record_id, record):
        """Drop ``record_id`` from every bucket ``record`` belongs to.

        Withdrawing a key the record was never filed under is not an
        error: the registry calls this while moving a record between
        keys, and the two key sets often overlap.
        """
        for key in keys_for(record, self.field, self.multi):
            bucket = self._buckets.get(key)
            if bucket is None:
                continue
            bucket.discard(record_id)
            if not bucket:
                del self._buckets[key]

    def lookup(self, key):
        """Ids filed under ``key``, in a stable order."""
        return sorted(self._buckets.get(key, ()))

    def keys(self):
        return sorted(self._buckets)

    def entries(self):
        return [(key, sorted(self._buckets[key])) for key in self.keys()]

    def cardinality(self):
        """How many distinct keys the index currently holds."""
        return len(self._buckets)

    def clear(self):
        self._buckets = {}

    def __contains__(self, key):
        return key in self._buckets

    def __len__(self):
        return sum(len(bucket) for bucket in self._buckets.values())

    def __repr__(self):
        return "HashIndex(%r, keys=%d)" % (self.field, len(self._buckets))
