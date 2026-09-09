"""Per-request scratch space that layers use to talk to each other."""

STATE_KEY = "context"


class Context:
    """A small typed bag stored on ``request.state``."""

    def __init__(self, values=None):
        self._values = dict(values or {})

    def set(self, name, value):
        self._values[name] = value
        return value

    def get(self, name, default=None):
        return self._values.get(name, default)

    def require(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise LookupError("no %r in the request context" % (name,)) from None

    def has(self, name):
        return name in self._values

    def update(self, values):
        self._values.update(values)
        return self

    def as_dict(self):
        return dict(self._values)

    def __contains__(self, name):
        return name in self._values

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return "Context(%r)" % (sorted(self._values),)


def context_of(request):
    """Fetch (creating on first use) the context attached to ``request``."""
    existing = request.state.get(STATE_KEY)
    if existing is None:
        existing = Context()
        request.state[STATE_KEY] = existing
    return existing
