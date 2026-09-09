"""The outbound response."""

import json

from .headers import HeaderMap
from .mediatype import HTML, JSON, TEXT
from .status import may_have_body, reason


class Response:
    """Status, headers and a byte body."""

    def __init__(self, body=b"", status=200, headers=None, media_type=None):
        self.status = status
        self.headers = headers if isinstance(headers, HeaderMap) else HeaderMap(headers)
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        if media_type is not None:
            self.headers.setdefault("Content-Type", str(media_type))

    @property
    def reason(self):
        return reason(self.status)

    def text(self):
        return self.body.decode("utf-8", "replace")

    def json(self):
        return json.loads(self.text())

    def header(self, name, value):
        self.headers.set(name, value)
        return self

    def seal(self):
        """Apply the rules that depend on the final status and body."""
        if not may_have_body(self.status):
            self.body = b""
            self.headers.remove("Content-Length")
        else:
            self.headers.setdefault("Content-Type", str(TEXT))
            self.headers.set("Content-Length", str(len(self.body)))
        return self

    def __repr__(self):
        return "<Response %d %s>" % (self.status, self.reason)


def json_response(payload, status=200, headers=None):
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return Response(body, status, headers, JSON)


def text_response(body, status=200, headers=None):
    return Response(body, status, headers, TEXT)


def html_response(body, status=200, headers=None):
    return Response(body, status, headers, HTML)


def empty(status=204):
    return Response(b"", status)
