"""The application object: registration, dispatch and error rendering."""

from httpkit.response import JsonResponse, Response
from routing.router import Router
from routing.urls import UrlBuilder

from .config import Config
from .errors import HttpError, PayloadTooLarge
from .hooks import HookRegistry
from .render import coerce_response


class Application:
    """Ties a router, a set of hooks and the error handlers together.

    A view is any callable taking the request and returning a ``Response``, a
    string, a JSON-able value or a ``(body, status)`` pair.
    """

    def __init__(self, config=None, **settings):
        if isinstance(config, Config):
            self.config = config.replace(**settings) if settings else config
        else:
            merged = dict(config or {})
            merged.update(settings)
            self.config = Config(**merged)
        self.router = Router()
        self.hooks = HookRegistry()
        self.urls = UrlBuilder(self.router, self.config.script_name)
        self._error_handlers = {}

    def add_route(self, template, handler, methods=("GET",), name=None):
        """Register one view."""
        return self.router.add(template, handler, methods, name)

    def route(self, template, methods=("GET",), name=None):
        """Decorator form of :meth:`add_route`."""

        def decorator(func):
            self.add_route(template, func, methods, name)
            return func

        return decorator

    def include(self, router, prefix=""):
        """Merge a separately built router into this application."""
        self.router.include(router, prefix)
        return self

    def before_request(self, func):
        return self.hooks.add_before(func)

    def after_request(self, func):
        return self.hooks.add_after(func)

    def error_handler(self, status):
        """Register a renderer for one status code."""

        def decorator(func):
            self._error_handlers[int(status)] = func
            return func

        return decorator

    def url_for(self, name, **values):
        return self.urls.url_for(name, **values)

    def handle(self, request):
        """Run one request through the stack and return a finished response."""
        error = None
        try:
            response = self._dispatch(request)
        except HttpError as exc:
            error = exc
            response = self.render_error(request, exc)
        except Exception as exc:  # pragma: no cover - re-raised while debugging
            if self.config.debug:
                raise
            error = HttpError(str(exc))
            response = self.render_error(request, error)
        response = self.hooks.run_after(request, response)
        self.hooks.run_teardown(request, error)
        return self._finish(request, response)

    def _dispatch(self, request):
        self._check_body_size(request)
        early = self.hooks.run_before(request)
        if early is not None:
            return coerce_response(early)
        route, params = self.router.match(request.method, request.path)
        request.path_params = params
        request.state["route"] = route.name
        return coerce_response(route.handler(request))

    def _check_body_size(self, request):
        limit = self.config.max_body_bytes
        if len(request.body) > limit:
            raise PayloadTooLarge(limit)

    def render_error(self, request, error):
        """Build the response for an ``HttpError``."""
        handler = self._error_handlers.get(error.status)
        if handler is not None:
            response = coerce_response(handler(request, error))
        elif self.config.json_errors:
            response = JsonResponse(error.payload(), error.status)
        else:
            response = Response(error.detail, error.status)
        response.status = error.status
        for name, value in error.headers.items():
            response.headers.set(name, value)
        return response

    def _finish(self, request, response):
        response.headers.setdefault("Server", self.config.server_name)
        if request.method == "HEAD":
            response.body = b""
        return response.finalize()

    def __repr__(self):
        return "<Application %d routes>" % len(self.router)
