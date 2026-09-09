"""A template bound to a handler."""

from .template import Template

READ_METHODS = frozenset(["GET", "HEAD"])


class Route:
    """One entry of a router."""

    def __init__(self, template, handler, methods=("GET",), name=None):
        self.template = Template(template)
        self.handler = handler
        methods = frozenset(method.upper() for method in methods)
        if "GET" in methods:
            methods = methods | {"HEAD"}
        self.methods = methods
        self.name = name or getattr(handler, "__name__", self.template.source)

    @property
    def source(self):
        return self.template.source

    @property
    def read_only(self):
        return self.methods <= READ_METHODS

    def match(self, path):
        return self.template.match(path)

    def accepts(self, method):
        return method.upper() in self.methods

    def build(self, **values):
        return self.template.build(values)

    def summary(self):
        return "%s %s" % ("|".join(sorted(self.methods)), self.source)

    def __repr__(self):
        return "<Route %s>" % self.summary()
