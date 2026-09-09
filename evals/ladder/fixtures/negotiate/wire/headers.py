"""A case-insensitive header mapping."""

from .params import split_commas


class Headers:
    """Header storage that keeps insertion order and allows repeats."""

    def __init__(self, initial=None):
        self._entries = []
        if initial:
            source = initial.items() if hasattr(initial, "items") else initial
            for name, value in source:
                self.append(name, value)

    def append(self, name, value):
        self._entries.append((name.lower(), name, str(value)))

    def put(self, name, value):
        self.discard(name)
        self.append(name, value)

    def default(self, name, value):
        if name not in self:
            self.append(name, value)
        return self.first(name)

    def discard(self, name):
        key = name.lower()
        self._entries = [entry for entry in self._entries if entry[0] != key]

    def first(self, name, default=None):
        key = name.lower()
        for entry in self._entries:
            if entry[0] == key:
                return entry[2]
        return default

    def every(self, name):
        key = name.lower()
        return [entry[2] for entry in self._entries if entry[0] == key]

    def listed(self, name):
        """Every comma separated element of a list-valued header."""
        values = []
        for raw in self.every(name):
            values.extend(split_commas(raw))
        return values

    def __contains__(self, name):
        key = name.lower()
        return any(entry[0] == key for entry in self._entries)

    def __getitem__(self, name):
        value = self.first(name)
        if value is None:
            raise KeyError(name)
        return value

    def __setitem__(self, name, value):
        self.put(name, value)

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        return iter((entry[1], entry[2]) for entry in self._entries)

    def items(self):
        return [(entry[1], entry[2]) for entry in self._entries]

    def names(self):
        seen = []
        for entry in self._entries:
            if entry[1] not in seen:
                seen.append(entry[1])
        return seen

    def copy(self):
        clone = Headers()
        clone._entries = list(self._entries)
        return clone

    def __repr__(self):
        return "Headers(%r)" % (self.items(),)


def vary(headers, *names):
    """Add names to the Vary header without duplicating what is there."""
    current = headers.listed("Vary")
    for name in names:
        if name not in current:
            current.append(name)
    if current:
        headers.put("Vary", ", ".join(current))
    return headers
