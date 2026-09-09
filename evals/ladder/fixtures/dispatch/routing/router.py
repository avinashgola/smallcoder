"""The route table and the lookup that turns a request into a handler."""

from core.errors import MethodNotAllowed, NotFound

from .patterns import normalize_path
from .route import Route


class Router:
    """Holds routes in registration order and resolves requests against them.

    Registration order matters: the first route whose pattern matches the
    requested path and whose method set contains the request method wins.
    """

    def __init__(self):
        self._routes = []
        self._by_name = {}

    def __len__(self):
        return len(self._routes)

    def __iter__(self):
        return iter(self._routes)

    def add(self, template, handler, methods=("GET",), name=None):
        """Register ``handler`` and return the created route."""
        route = Route(template, handler, methods, name)
        if route.name in self._by_name:
            raise ValueError("duplicate route name %r" % (route.name,))
        self._routes.append(route)
        self._by_name[route.name] = route
        return route

    def include(self, other, prefix=""):
        """Copy every route from ``other`` in, optionally under a prefix."""
        prefix = normalize_path(prefix) if prefix else ""
        if prefix == "/":
            prefix = ""
        for route in other:
            template = prefix + route.template
            self.add(template, route.handler, route.methods, route.name)
        return self

    def match(self, method, path):
        """Resolve ``method path`` to a ``(route, params)`` pair.

        Raises ``MethodNotAllowed`` when the path is served by routes that do
        not accept this method, and ``NotFound`` when nothing matches at all.
        """
        method = method.upper()
        target = normalize_path(path)
        allowed = set()
        for route in self._routes:
            params = route.match(target)
            if params is None:
                continue
            allowed.update(route.methods)
            if not route.accepts(method):
                raise MethodNotAllowed(sorted(allowed))
            return route, params
        raise NotFound(path)

    def methods_for(self, path):
        """Every method served on ``path``, for ``OPTIONS`` replies."""
        target = normalize_path(path)
        allowed = set()
        for route in self._routes:
            if route.match(target) is not None:
                allowed.update(route.methods)
        return sorted(allowed)

    def get(self, name):
        try:
            return self._by_name[name]
        except KeyError:
            raise KeyError("no route named %r" % (name,)) from None

    def describe(self):
        return [route.describe() for route in self._routes]
