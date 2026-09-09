"""The inbound request object handed to every view."""

import json

from .cookies import parse_cookie_header
from .headers import Headers, parse_options
from .query import QueryParams

SAFE_METHODS = frozenset(["GET", "HEAD", "OPTIONS", "TRACE"])
BODY_METHODS = frozenset(["POST", "PUT", "PATCH", "DELETE"])


class Request:
    """An immutable-ish view of one inbound HTTP request.

    ``path_params`` is filled in by the router once a route has been chosen;
    views read it instead of parsing the path themselves.
    """

    def __init__(self, method="GET", path="/", headers=None, query="",
                 body=b"", remote_addr="127.0.0.1"):
        self.method = method.upper()
        self.path = path
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        self.query = QueryParams(query)
        self.body = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.remote_addr = remote_addr
        self.path_params = {}
        self.state = {}

    @property
    def is_safe(self):
        return self.method in SAFE_METHODS

    @property
    def content_type(self):
        media, _ = parse_options(self.headers.get("Content-Type"))
        return media

    @property
    def charset(self):
        _, options = parse_options(self.headers.get("Content-Type"))
        return options.get("charset", "utf-8")

    @property
    def content_length(self):
        raw = self.headers.get("Content-Length")
        if raw is None:
            return len(self.body)
        try:
            return int(raw)
        except ValueError:
            return len(self.body)

    @property
    def cookies(self):
        return parse_cookie_header(self.headers.get("Cookie"))

    def text(self):
        return self.body.decode(self.charset, "replace")

    def json(self):
        """Decode the body as JSON, or return ``None`` when it is empty."""
        if not self.body:
            return None
        return json.loads(self.text())

    def header(self, name, default=None):
        return self.headers.get(name, default)

    def param(self, name, default=None):
        """A path parameter captured by the matched route."""
        return self.path_params.get(name, default)

    def with_path(self, path):
        """A shallow copy pointing at a different path, used when mounting."""
        clone = Request(self.method, path, self.headers.copy(),
                        self.query.raw, self.body, self.remote_addr)
        clone.state = self.state
        return clone

    def __repr__(self):
        return "<Request %s %s>" % (self.method, self.path)
