"""In-process client."""

import json

from wire.headers import Headers
from wire.request import Request


class Client:
    """Calls a server directly, no socket involved."""

    def __init__(self, server, headers=None):
        self.server = server
        self.headers = Headers(headers)

    def open(self, method, path, headers=None, query="", body=b"", json_body=None):
        merged = self.headers.copy()
        for name, value in (headers.items() if hasattr(headers, "items")
                            else (headers or [])):
            merged.put(name, value)
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            merged.put("Content-Type", "application/json")
        return self.server.handle(Request(method, path, merged, query, body))

    def get(self, path, **kwargs):
        return self.open("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.open("POST", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.open("DELETE", path, **kwargs)
