"""An in-process client for tests."""

import json

from message.headers import HeaderMap
from message.request import Request


class Client:
    """Drives an application without a socket in between."""

    def __init__(self, app, headers=None):
        self.app = app
        self.headers = HeaderMap(headers)

    def open(self, method, path, headers=None, query="", body=b"", json_body=None):
        merged = self.headers.copy()
        if headers:
            merged.merge(headers)
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            merged.set("Content-Type", "application/json")
        return self.app.handle(Request(method, path, merged, query, body))

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
