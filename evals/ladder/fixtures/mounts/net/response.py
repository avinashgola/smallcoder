"""The response object and the shorthands handlers use."""

import json

from .headers import Headers
from .status import has_body, is_redirect, reason


class Response:
    """Status, headers and body bytes."""

    def __init__(self, body=b"", status=200, headers=None, content_type=None):
        self.status = status
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        if content_type:
            self.headers.fallback("Content-Type", content_type)

    @property
    def reason(self):
        return reason(self.status)

    def text(self):
        return self.body.decode("utf-8", "replace")

    def json_body(self):
        return json.loads(self.text())

    def finish(self):
        """Settle the headers that depend on the final body."""
        if has_body(self.status):
            self.headers.fallback("Content-Type", "text/plain; charset=utf-8")
            self.headers.assign("Content-Length", str(len(self.body)))
        else:
            self.body = b""
            self.headers.drop("Content-Length")
        return self

    def __repr__(self):
        return "<Response %d %s>" % (self.status, self.reason)


def json_response(payload, status=200, headers=None):
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return Response(body, status, headers, "application/json")


def text_response(body, status=200, headers=None):
    return Response(body, status, headers, "text/plain; charset=utf-8")


def html_response(body, status=200, headers=None):
    return Response(body, status, headers, "text/html; charset=utf-8")


def redirect(location, status=302):
    if not is_redirect(status):
        raise ValueError("%r is not a redirect status" % (status,))
    response = Response(b"", status)
    response.headers.assign("Location", location)
    return response
