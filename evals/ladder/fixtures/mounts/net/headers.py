"""Header storage: a list of pairs with case-insensitive lookup."""


class Headers:
    """Ordered header pairs; names may repeat."""

    def __init__(self, initial=None):
        self._pairs = []
        if initial:
            source = initial.items() if hasattr(initial, "items") else initial
            for name, value in source:
                self.append(name, value)

    def append(self, name, value):
        self._pairs.append((name, str(value)))

    def assign(self, name, value):
        key = name.lower()
        self._pairs = [pair for pair in self._pairs if pair[0].lower() != key]
        self.append(name, value)

    def fallback(self, name, value):
        """Set the header only if it is not present already."""
        if name not in self:
            self.append(name, value)
        return self.first(name)

    def drop(self, name):
        key = name.lower()
        self._pairs = [pair for pair in self._pairs if pair[0].lower() != key]

    def first(self, name, default=None):
        key = name.lower()
        for existing, value in self._pairs:
            if existing.lower() == key:
                return value
        return default

    def all(self, name):
        key = name.lower()
        return [value for existing, value in self._pairs
                if existing.lower() == key]

    def __contains__(self, name):
        key = name.lower()
        return any(existing.lower() == key for existing, _ in self._pairs)

    def __getitem__(self, name):
        value = self.first(name)
        if value is None:
            raise KeyError(name)
        return value

    def __setitem__(self, name, value):
        self.assign(name, value)

    def __len__(self):
        return len(self._pairs)

    def __iter__(self):
        return iter(self._pairs)

    def items(self):
        return list(self._pairs)

    def copy(self):
        clone = Headers()
        clone._pairs = list(self._pairs)
        return clone

    def merge(self, other):
        source = other.items() if hasattr(other, "items") else other
        for name, value in source:
            self.assign(name, value)
        return self

    def __repr__(self):
        return "Headers(%r)" % (self._pairs,)
