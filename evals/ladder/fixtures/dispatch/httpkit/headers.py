"""A case-insensitive, multi-value header collection."""


def normalize(name):
    """Canonical comparison form of a header name."""
    return name.strip().lower()


def titlecase(name):
    """Render a header name the way it is conventionally sent on the wire."""
    return "-".join(part.capitalize() for part in normalize(name).split("-"))


class Headers:
    """Ordered, case-insensitive headers that may repeat a name.

    Lookup is case-insensitive but the casing used by the caller is kept so
    that responses go out looking the way the application wrote them.
    """

    def __init__(self, values=None):
        self._items = []
        if values is not None:
            self.update(values)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(name for _, name, _ in self._items)

    def __contains__(self, name):
        key = normalize(name)
        return any(k == key for k, _, _ in self._items)

    def __getitem__(self, name):
        key = normalize(name)
        for k, _, value in self._items:
            if k == key:
                return value
        raise KeyError(name)

    def __setitem__(self, name, value):
        self.set(name, value)

    def __delitem__(self, name):
        key = normalize(name)
        kept = [item for item in self._items if item[0] != key]
        if len(kept) == len(self._items):
            raise KeyError(name)
        self._items = kept

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def get_all(self, name):
        """Every value stored under ``name``, in insertion order."""
        key = normalize(name)
        return [value for k, _, value in self._items if k == key]

    def add(self, name, value):
        """Append a value without removing values already stored."""
        self._items.append((normalize(name), name, str(value)))

    def set(self, name, value):
        """Replace every value stored under ``name``."""
        key = normalize(name)
        replaced = False
        items = []
        for item in self._items:
            if item[0] != key:
                items.append(item)
            elif not replaced:
                items.append((key, name, str(value)))
                replaced = True
        if not replaced:
            items.append((key, name, str(value)))
        self._items = items

    def setdefault(self, name, value):
        if name not in self:
            self.set(name, value)
        return self[name]

    def pop(self, name, *default):
        try:
            value = self[name]
        except KeyError:
            if default:
                return default[0]
            raise
        del self[name]
        return value

    def update(self, values):
        if isinstance(values, Headers):
            pairs = values.items()
        elif hasattr(values, "items"):
            pairs = list(values.items())
        else:
            pairs = list(values)
        for name, value in pairs:
            self.set(name, value)

    def items(self):
        return [(name, value) for _, name, value in self._items]

    def keys(self):
        return [name for _, name, _ in self._items]

    def values(self):
        return [value for _, _, value in self._items]

    def to_wire(self):
        """Header pairs with canonical casing, ready to be serialised."""
        return [(titlecase(name), value) for _, name, value in self._items]

    def copy(self):
        clone = Headers()
        clone._items = list(self._items)
        return clone

    def __repr__(self):
        return "Headers(%r)" % (self.items(),)


def parse_options(value):
    """Split ``text/html; charset=utf-8`` into its value and its parameters."""
    if value is None:
        return None, {}
    parts = value.split(";")
    main = parts[0].strip()
    options = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, _, raw = part.partition("=")
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            raw = raw[1:-1]
        options[key.strip().lower()] = raw
    return main, options
