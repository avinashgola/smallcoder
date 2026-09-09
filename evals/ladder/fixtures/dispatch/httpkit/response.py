"""Response objects and the small helpers views use to build them."""

import json

from .headers import Headers
from .status import allows_body, phrase


class Response:
    """A status code, a set of headers and a byte body."""

    default_content_type = "text/plain; charset=utf-8"

    def __init__(self, body=b"", status=200, headers=None, content_type=None):
        self.status = status
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.body = body
        if not allows_body(status):
            self.body = b""
        if "Content-Type" not in self.headers:
            self.headers.set("Content-Type", content_type or self.default_content_type)

    @property
    def reason(self):
        return phrase(self.status)

    def text(self):
        return self.body.decode("utf-8", "replace")

    def set_cookie(self, value):
        self.headers.add("Set-Cookie", value)
        return self

    def with_header(self, name, value):
        self.headers.set(name, value)
        return self

    def finalize(self):
        """Fill in the headers that depend on the finished body."""
        if allows_body(self.status):
            self.headers.set("Content-Length", str(len(self.body)))
        else:
            self.body = b""
            self.headers.pop("Content-Length", None)
        return self

    def __repr__(self):
        return "<Response %d %s>" % (self.status, self.reason)


class JsonResponse(Response):
    """A response whose body is a JSON document."""

    def __init__(self, payload, status=200, headers=None):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        super().__init__(body, status, headers, "application/json")
        self.payload = payload


def text(body, status=200, headers=None):
    return Response(body, status, headers, "text/plain; charset=utf-8")


def html(body, status=200, headers=None):
    return Response(body, status, headers, "text/html; charset=utf-8")


def no_content():
    return Response(b"", 204)


def redirect(location, status=302):
    """A redirect response pointing at ``location``."""
    if status not in (301, 302, 303, 307, 308):
        raise ValueError("not a redirect status: %r" % (status,))
    response = Response(b"", status)
    response.headers.set("Location", location)
    return response
