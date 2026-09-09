"""The layers that ship with the framework."""

from message.headers import split_list
from message.response import Response, json_response
from message.urls import starts_with
from web.errors import HttpError, UnsupportedMediaType

from .base import Layer
from .context import context_of

SAFE_DEFAULTS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


class ResponseHeader(Layer):
    """Stamps one fixed header onto every response."""

    def __init__(self, name, value):
        self.name = "ResponseHeader(%s)" % name
        self.header = name
        self.value = value

    def __call__(self, request, next_layer):
        response = next_layer(request)
        response.headers.set(self.header, self.value)
        return response


class SecurityHeaders(Layer):
    """Adds the hardening headers, without overwriting explicit ones."""

    def __init__(self, **overrides):
        self.values = dict(SAFE_DEFAULTS)
        self.values.update(overrides)

    def __call__(self, request, next_layer):
        response = next_layer(request)
        for name, value in sorted(self.values.items()):
            response.headers.setdefault(name, value)
        return response


class RequestId(Layer):
    """Echoes an inbound correlation id, or labels the request as untracked."""

    def __init__(self, header="X-Request-Id", fallback="untracked"):
        self.header = header
        self.fallback = fallback

    def __call__(self, request, next_layer):
        value = request.headers.get(self.header) or self.fallback
        context_of(request).set("request_id", value)
        response = next_layer(request)
        response.headers.setdefault(self.header, value)
        return response


class ErrorEnvelope(Layer):
    """Turns raised :class:`HttpError` instances into JSON responses."""

    def __init__(self, include_detail=True):
        self.include_detail = include_detail

    def __call__(self, request, next_layer):
        try:
            return next_layer(request)
        except HttpError as error:
            payload = error.as_dict()
            if not self.include_detail:
                payload.pop("detail", None)
            response = json_response(payload, error.status)
            for name, value in error.headers.items():
                response.headers.set(name, value)
            return response


class RequireJson(Layer):
    """Rejects bodies that are not JSON on the methods that carry one."""

    methods = ("POST", "PUT", "PATCH")

    def __init__(self, methods=None):
        if methods is not None:
            self.methods = tuple(method.upper() for method in methods)

    def __call__(self, request, next_layer):
        if request.method in self.methods and request.body:
            media = request.media_type
            if media is None or media.essence != "application/json":
                raise UnsupportedMediaType(
                    str(media) if media else "nothing", "application/json")
        return next_layer(request)


class StripPrefix(Layer):
    """Serves an application that is deployed under a path prefix."""

    def __init__(self, prefix):
        self.prefix = prefix.rstrip("/")

    def __call__(self, request, next_layer):
        if not self.prefix or not starts_with(request.path, self.prefix):
            return next_layer(request)
        rest = request.path[len(self.prefix):] or "/"
        return next_layer(request.rewrite(rest))


class Cors(Layer):
    """A deliberately small CORS layer: exact origins only, no credentials."""

    def __init__(self, origins=("*",), methods=("GET", "POST"), max_age=600):
        self.origins = tuple(origins)
        self.methods = tuple(method.upper() for method in methods)
        self.max_age = max_age

    def allowed(self, origin):
        return origin is not None and ("*" in self.origins
                                       or origin in self.origins)

    def __call__(self, request, next_layer):
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and "Access-Control-Request-Method" in request.headers:
            return self.preflight(request, origin)
        response = next_layer(request)
        if self.allowed(origin):
            response.headers.set("Access-Control-Allow-Origin", origin)
            response.headers.set("Vary", "Origin")
        return response

    def preflight(self, request, origin):
        response = Response(b"", 204)
        if not self.allowed(origin):
            return response
        wanted = request.headers.get("Access-Control-Request-Method", "")
        if wanted.upper() not in self.methods:
            return response
        response.headers.set("Access-Control-Allow-Origin", origin)
        response.headers.set("Access-Control-Allow-Methods", ", ".join(self.methods))
        requested = split_list(request.headers.get("Access-Control-Request-Headers"))
        if requested:
            response.headers.set("Access-Control-Allow-Headers", ", ".join(requested))
        response.headers.set("Access-Control-Max-Age", str(self.max_age))
        return response


class AccessLog(Layer):
    """Appends one record per request to a caller-supplied list."""

    def __init__(self, sink):
        self.sink = sink

    def __call__(self, request, next_layer):
        response = next_layer(request)
        self.sink.append("%s %s -> %d" % (request.method, request.path,
                                          response.status))
        return response
