"""An in-process client so tests can exercise an application directly."""

import json

from httpkit.headers import Headers
from httpkit.request import Request


class Client:
    """Sends requests to an application without going near a socket."""

    def __init__(self, app, base_headers=None):
        self.app = app
        self.base_headers = Headers(base_headers)

    def open(self, method, path, headers=None, query="", body=b"", json_body=None):
        merged = self.base_headers.copy()
        if headers:
            merged.update(headers)
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            merged.set("Content-Type", "application/json")
        request = Request(method, path, merged, query, body)
        return self.app.handle(request)

    def get(self, path, **kwargs):
        return self.open("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.open("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.open("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.open("DELETE", path, **kwargs)

    def options(self, path, **kwargs):
        return self.open("OPTIONS", path, **kwargs)


def payload_of(response):
    """Decode a JSON response body in tests."""
    return json.loads(response.text())
