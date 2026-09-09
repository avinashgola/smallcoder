"""The response object."""

import json

from .headers import Headers
from .status import OK, bodyless, reason


class Response:
    """Status, headers and an encoded body."""

    def __init__(self, body=b"", status=OK, headers=None, content_type=None):
        self.status = status
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        if content_type:
            self.headers.default("Content-Type", content_type)

    @property
    def reason(self):
        return reason(self.status)

    @property
    def content_type(self):
        return self.headers.first("Content-Type")

    def text(self):
        return self.body.decode("utf-8", "replace")

    def json_body(self):
        return json.loads(self.text())

    def close(self):
        """Apply the final header rules once the body is settled."""
        if bodyless(self.status):
            self.body = b""
            self.headers.discard("Content-Length")
        else:
            self.headers.put("Content-Length", str(len(self.body)))
        return self

    def __repr__(self):
        return "<Response %d %s>" % (self.status, self.reason)
