"""The application object."""

from message.request import Request
from message.response import Response, json_response, text_response
from middleware.chain import Chain

from .config import Settings
from .errors import HttpError
from .routing import RouteTable


def to_response(result):
    """Coerce whatever an endpoint returned into a response."""
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
    raise TypeError("endpoints cannot return %r" % (type(result).__name__,))


class Application:
    """Routes plus a middleware chain.

    Layers are added with :meth:`use` and run in the order they were added,
    wrapped around the endpoint the route table picked.
    """

    def __init__(self, settings=None, **overrides):
        if isinstance(settings, Settings):
            self.settings = settings.replace(**overrides) if overrides else settings
        else:
            merged = dict(settings or {})
            merged.update(overrides)
            self.settings = Settings(**merged)
        self.routes = RouteTable()
        self.middleware = Chain()

    def use(self, layer):
        """Add one middleware layer, outermost first."""
        self.middleware.add(layer)
        return self

    def add(self, template, endpoint, methods=("GET",), name=None):
        return self.routes.add(template, endpoint, methods, name)

    def get(self, template, endpoint, name=None):
        return self.add(template, endpoint, ("GET",), name)

    def post(self, template, endpoint, name=None):
        return self.add(template, endpoint, ("POST",), name)

    def put(self, template, endpoint, name=None):
        return self.add(template, endpoint, ("PUT",), name)

    def delete(self, template, endpoint, name=None):
        return self.add(template, endpoint, ("DELETE",), name)

    def handle(self, request):
        """Run one request through the middleware chain and the router."""
        handler = self.middleware.build(self.resolve)
        try:
            response = to_response(handler(request))
        except HttpError as error:
            response = self.render_error(error)
        return response.seal()

    def resolve(self, request):
        """The innermost endpoint: route the request and call the view."""
        rule, params = self.routes.find(request.method, request.path)
        request.params = params
        request.state["rule"] = rule.name
        return to_response(rule.endpoint(request))

    def render_error(self, error):
        response = json_response(error.as_dict(), error.status)
        for name, value in error.headers.items():
            response.headers.set(name, value)
        return response

    def request(self, method, path, **kwargs):
        """Build and run a request in one call, mostly useful in scripts."""
        return self.handle(Request(method, path, **kwargs))

    def __repr__(self):
        return "<Application %d rules, %d layers>" % (
            len(self.routes), len(self.middleware))
