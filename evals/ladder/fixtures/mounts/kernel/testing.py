"""An in-process client."""

import json

from net.headers import Headers
from net.request import Request


class Client:
    """Sends requests straight into an application.

    The client is the piece that behaves like a browser: it makes sure the
    request target it sends is absolute.
    """

    def __init__(self, app, headers=None):
        self.app = app
        self.headers = Headers(headers)

    def open(self, method, path, headers=None, query="", body=b"", json_body=None):
        if not path.startswith("/"):
            path = "/" + path
        merged = self.headers.copy()
        if headers:
            merged.merge(headers)
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            merged.assign("Content-Type", "application/json")
        return self.app.handle(Request(method, path, merged, query, body))

    def get(self, path, **kwargs):
        return self.open("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.open("POST", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.open("DELETE", path, **kwargs)
