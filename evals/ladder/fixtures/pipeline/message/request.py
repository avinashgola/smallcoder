"""The inbound request."""

import json

from .headers import HeaderMap
from .mediatype import parse_media_type
from .urls import normalize, parse_query


class Request:
    """One inbound request, plus the per-request scratch space middleware use."""

    def __init__(self, method="GET", path="/", headers=None, query="", body=b""):
        self.method = method.upper()
        self.path = normalize(path)
        self.headers = headers if isinstance(headers, HeaderMap) else HeaderMap(headers)
        self.query_string = query.lstrip("?") if query else ""
        self.body = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.params = {}
        self.state = {}
        self._query = None

    @property
    def query(self):
        if self._query is None:
            self._query = parse_query(self.query_string)
        return self._query

    def arg(self, name, default=None):
        for key, value in self.query:
            if key == name:
                return value
        return default

    def arg_int(self, name, default=None):
        raw = self.arg(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    def param(self, name, default=None):
        return self.params.get(name, default)

    @property
    def media_type(self):
        return parse_media_type(self.headers.get("Content-Type"))

    @property
    def charset(self):
        media = self.media_type
        return (media.charset if media else None) or "utf-8"

    def text(self):
        return self.body.decode(self.charset, "replace")

    def json(self):
        if not self.body:
            return None
        return json.loads(self.text())

    def rewrite(self, path):
        """A copy pointing at another path, sharing the per-request state."""
        clone = Request(self.method, path, self.headers.copy(),
                        self.query_string, self.body)
        clone.state = self.state
        clone.params = dict(self.params)
        return clone

    def __repr__(self):
        return "<Request %s %s>" % (self.method, self.path)
