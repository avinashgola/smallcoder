"""The request object."""

import json

from .headers import Headers
from .params import split_params
from .urls import query_pairs, tidy


class Request:
    """One inbound request."""

    def __init__(self, method="GET", path="/", headers=None, query="", body=b""):
        self.method = method.upper()
        self.path = tidy(path)
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        self.query_string = query[1:] if query.startswith("?") else query
        self.body = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.args = query_pairs(self.query_string)
        self.vars = {}
        self.notes = {}

    def arg(self, name, default=None):
        for key, value in self.args:
            if key == name:
                return value
        return default

    def arg_list(self, name):
        return [value for key, value in self.args if key == name]

    def var(self, name, default=None):
        return self.vars.get(name, default)

    def accept(self):
        """The raw Accept header, or ``None`` when the client sent none."""
        return self.headers.first("Accept")

    def content_type(self):
        head, _ = split_params(self.headers.first("Content-Type") or "")
        return head.lower() or None

    def charset(self, default="utf-8"):
        _, params = split_params(self.headers.first("Content-Type") or "")
        return params.get("charset", default)

    def text(self):
        return self.body.decode(self.charset(), "replace")

    def json(self):
        if not self.body:
            return None
        return json.loads(self.text())

    def __repr__(self):
        return "<Request %s %s>" % (self.method, self.path)
