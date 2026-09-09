"""The per-application router."""

from kernel.errors import MethodNotAllowed, NotFound
from net.request import clean

from .route import Route


class Router:
    """Routes searched in registration order.

    Paths are matched from their first character, so a router only ever sees
    absolute paths: an application mounted under a prefix is handed the part
    of the path below that prefix, still rooted with a slash.
    """

    def __init__(self):
        self.routes = []

    def __len__(self):
        return len(self.routes)

    def __iter__(self):
        return iter(self.routes)

    def add(self, template, handler, methods=("GET",), name=None):
        route = Route(template, handler, methods, name)
        self.routes.append(route)
        return route

    def find(self, method, path):
        """Return ``(route, captured)`` or raise the right HTTP error."""
        target = clean(path)
        allowed = set()
        for route in self.routes:
            captured = route.match(target)
            if captured is None:
                continue
            if not route.accepts(method):
                allowed.update(route.methods)
                continue
            return route, captured
        if allowed:
            raise MethodNotAllowed(allowed)
        raise NotFound(path)

    def named(self, name):
        for route in self.routes:
            if route.name == name:
                return route
        raise KeyError(name)

    def sources(self):
        return [route.source for route in self.routes]

    def summaries(self):
        return [route.summary() for route in self.routes]
