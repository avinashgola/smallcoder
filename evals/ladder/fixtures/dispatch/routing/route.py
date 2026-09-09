"""A single entry in the route table."""

from .patterns import Pattern

DEFAULT_METHODS = ("GET",)


def _clean_methods(methods):
    cleaned = set()
    for method in methods:
        method = method.strip().upper()
        if not method:
            raise ValueError("empty HTTP method")
        cleaned.add(method)
    if "GET" in cleaned:
        cleaned.add("HEAD")
    return frozenset(cleaned)


class Route:
    """Binds a compiled pattern and a set of methods to one handler."""

    def __init__(self, template, handler, methods=DEFAULT_METHODS, name=None):
        self.pattern = Pattern(template)
        self.handler = handler
        self.methods = _clean_methods(methods)
        self.name = name or getattr(handler, "__name__", None) or self.template

    @property
    def template(self):
        return self.pattern.template

    @property
    def parameter_names(self):
        return self.pattern.parameter_names

    def match(self, path):
        """Captured parameters for ``path``, or ``None``."""
        return self.pattern.match(path)

    def accepts(self, method):
        return method.upper() in self.methods

    def build(self, **values):
        return self.pattern.build(values)

    def describe(self):
        return "%s %s -> %s" % (
            ",".join(sorted(self.methods)), self.template, self.name)

    def __repr__(self):
        return "<Route %s>" % self.describe()
