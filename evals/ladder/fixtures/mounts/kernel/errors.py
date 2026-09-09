"""Errors with a status code attached."""


class HttpError(Exception):
    """Base class for anything the server answers with 4xx or 5xx."""

    status = 500
    slug = "server_error"

    def __init__(self, detail=None, headers=None):
        super().__init__(detail or self.slug)
        self.detail = detail
        self.headers = dict(headers or {})

    def payload(self):
        body = {"error": self.slug, "status": self.status}
        if self.detail:
            body["detail"] = self.detail
        return body


class BadRequest(HttpError):
    status = 400
    slug = "bad_request"


class Unauthorized(HttpError):
    status = 401
    slug = "unauthorized"

    def __init__(self, detail=None, realm="admin"):
        super().__init__(detail, {"WWW-Authenticate": 'Basic realm="%s"' % realm})


class Forbidden(HttpError):
    status = 403
    slug = "forbidden"


class NotFound(HttpError):
    status = 404
    slug = "not_found"

    def __init__(self, path=None):
        self.path = path
        super().__init__("nothing serves %s" % path if path else None)

    def payload(self):
        body = super().payload()
        if self.path:
            body["path"] = self.path
        return body


class MethodNotAllowed(HttpError):
    status = 405
    slug = "method_not_allowed"

    def __init__(self, allowed):
        self.allowed = sorted(allowed)
        joined = ", ".join(self.allowed)
        super().__init__("allowed: " + joined, {"Allow": joined})


class Conflict(HttpError):
    status = 409
    slug = "conflict"


class Invalid(HttpError):
    status = 422
    slug = "invalid"

    def __init__(self, fields):
        self.fields = dict(fields)
        super().__init__("invalid: " + ", ".join(sorted(self.fields)))

    def payload(self):
        body = super().payload()
        body["fields"] = self.fields
        return body
