"""Header storage.

Values are kept in a dict keyed by the lower-cased name so lookups are cheap;
the casing the caller used is remembered separately for serialisation.
"""


class HeaderMap:
    """A multi-value mapping with case-insensitive keys."""

    def __init__(self, initial=None):
        self._values = {}
        self._casing = {}
        self._order = []
        if initial:
            for name, value in _pairs(initial):
                self.add(name, value)

    def add(self, name, value):
        key = name.lower()
        if key not in self._values:
            self._values[key] = []
            self._casing[key] = name
            self._order.append(key)
        self._values[key].append(str(value))

    def set(self, name, value):
        key = name.lower()
        if key in self._values:
            self._values[key] = [str(value)]
            self._casing[key] = name
        else:
            self.add(name, value)

    def setdefault(self, name, value):
        key = name.lower()
        if key not in self._values:
            self.add(name, value)
        return self._values[key][0]

    def get(self, name, default=None):
        values = self._values.get(name.lower())
        return values[0] if values else default

    def get_all(self, name):
        return list(self._values.get(name.lower(), ()))

    def remove(self, name):
        key = name.lower()
        self._values.pop(key, None)
        self._casing.pop(key, None)
        if key in self._order:
            self._order.remove(key)

    def __contains__(self, name):
        return name.lower() in self._values

    def __getitem__(self, name):
        try:
            return self._values[name.lower()][0]
        except (KeyError, IndexError):
            raise KeyError(name) from None

    def __setitem__(self, name, value):
        self.set(name, value)

    def __len__(self):
        return sum(len(values) for values in self._values.values())

    def __iter__(self):
        for key in self._order:
            for value in self._values[key]:
                yield self._casing[key], value

    def names(self):
        return [self._casing[key] for key in self._order]

    def items(self):
        return list(iter(self))

    def copy(self):
        clone = HeaderMap()
        clone._values = {key: list(values) for key, values in self._values.items()}
        clone._casing = dict(self._casing)
        clone._order = list(self._order)
        return clone

    def merge(self, other):
        for name, value in _pairs(other):
            self.set(name, value)
        return self

    def __repr__(self):
        return "HeaderMap(%r)" % (self.items(),)


def _pairs(source):
    if isinstance(source, HeaderMap):
        return source.items()
    if hasattr(source, "items"):
        return list(source.items())
    return list(source)


def split_list(value):
    """Split a comma separated header value into stripped, non-empty parts."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]
