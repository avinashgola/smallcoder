"""The application object: routes, mounts and dispatch."""

from mounting.table import MountTable
from net.response import Response, json_response, text_response
from routes.router import Router

from .config import Settings
from .errors import HttpError


def to_response(result):
    """Coerce a handler's return value into a response."""
    if isinstance(result, Response):
        return result
    if result is None:
        return Response(b"", 204)
    if isinstance(result, (dict, list)):
        return json_response(result)
    if isinstance(result, tuple) and len(result) == 2:
        body, status = result
        response = to_response(body)
        response.status = status
        return response
    if isinstance(result, (str, bytes)):
        return text_response(result)
    raise TypeError("a handler cannot return %r" % (type(result).__name__,))


class Application:
    """A router, a mount table and the dispatch that ties them together.

    An application can be served on its own or mounted inside another one.
    When it is mounted, it is handed the part of the path below its prefix
    and never sees the prefix itself.
    """

    def __init__(self, name="app", settings=None, **overrides):
        self.name = name
        if isinstance(settings, Settings):
            self.settings = settings.child(**overrides) if overrides else settings
        else:
            merged = dict(settings or {})
            merged.update(overrides)
            self.settings = Settings(**merged)
        self.router = Router()
        self.mounts = MountTable()

    def route(self, template, handler, methods=("GET",), name=None):
        return self.router.add(template, handler, methods, name)

    def get(self, template, handler, name=None):
        return self.route(template, handler, ("GET",), name)

    def post(self, template, handler, name=None):
        return self.route(template, handler, ("POST",), name)

    def delete(self, template, handler, name=None):
        return self.route(template, handler, ("DELETE",), name)

    def mount(self, prefix, app, name=None):
        """Serve another application below ``prefix``."""
        return self.mounts.add(prefix, app, name)

    def dispatch(self, request):
        """Resolve the request, letting HTTP errors travel to the top."""
        found = self.mounts.resolve(request.path)
        if found is not None:
            mount, inner = found
            request.notes.setdefault("mounts", []).append(mount.name)
            return mount.app.dispatch(request.relocate(inner, mount.prefix))
        route, captured = self.router.find(request.method, request.path)
        request.vars = captured
        request.notes["route"] = route.name
        request.notes["app"] = self.name
        return to_response(route.handler(request))

    def handle(self, request):
        """Run one request all the way to a finished response."""
        try:
            response = self.dispatch(request)
        except HttpError as error:
            response = self.render_error(error)
        response.headers.fallback("Server", self.settings.server_token)
        if request.method == "HEAD":
            response.body = b""
        return response.finish()

    def render_error(self, error):
        if self.settings.json_errors:
            response = json_response(error.payload(), error.status)
        else:
            response = text_response(error.detail or error.slug, error.status)
        for name, value in error.headers.items():
            response.headers.assign(name, value)
        return response

    def __repr__(self):
        return "<Application %s: %d routes, %d mounts>" % (
            self.name, len(self.router), len(self.mounts))
