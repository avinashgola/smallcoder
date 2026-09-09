"""Counting helpers used while summarising a run."""


class Tally:
    """An insertion ordered counter."""

    def __init__(self, items=None, key=None):
        self._counts = {}
        self._order = []
        if items is not None:
            self.add_all(items, key=key)

    def add(self, name, amount=1):
        if name not in self._counts:
            self._counts[name] = 0
            self._order.append(name)
        self._counts[name] += amount
        return self._counts[name]

    def add_all(self, items, key=None):
        for item in items:
            self.add(key(item) if key else item)
        return self

    def get(self, name, default=0):
        return self._counts.get(name, default)

    def names(self):
        return list(self._order)

    def items(self):
        return [(name, self._counts[name]) for name in self._order]

    def as_dict(self):
        return dict(self._counts)

    def total(self):
        return sum(self._counts.values())

    def most_common(self, limit=None):
        ranked = sorted(self.items(), key=lambda pair: (-pair[1], pair[0]))
        return ranked if limit is None else ranked[:limit]

    def __len__(self):
        return len(self._order)

    def __contains__(self, name):
        return name in self._counts


def sum_by(items, key, value):
    """Sum `value(item)` per `key(item)`, in first-seen key order."""
    tally = Tally()
    for item in items:
        tally.add(key(item), value(item))
    return tally
