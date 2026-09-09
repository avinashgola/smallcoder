"""Errors that carry a status code and a machine readable code."""


class HttpError(Exception):
    """Base class: everything the application answers with 4xx/5xx."""

    status = 500
    code = "internal_error"

    def __init__(self, detail=None, headers=None):
        super().__init__(detail or self.code)
        self.detail = detail
        self.headers = dict(headers or {})

    def as_dict(self):
        payload = {"code": self.code, "status": self.status}
        if self.detail:
            payload["detail"] = self.detail
        return payload


class BadRequest(HttpError):
    status = 400
    code = "bad_request"


class Unauthorized(HttpError):
    status = 401
    code = "unauthorized"


class Forbidden(HttpError):
    status = 403
    code = "forbidden"


class NotFound(HttpError):
    status = 404
    code = "not_found"

    def __init__(self, path=None):
        self.path = path
        super().__init__("nothing serves %s" % path if path else None)

    def as_dict(self):
        payload = super().as_dict()
        if self.path:
            payload["path"] = self.path
        return payload


class MethodNotAllowed(HttpError):
    status = 405
    code = "method_not_allowed"

    def __init__(self, allowed):
        self.allowed = sorted(allowed)
        joined = ", ".join(self.allowed)
        super().__init__("try " + joined, {"Allow": joined})


class Conflict(HttpError):
    status = 409
    code = "conflict"


class UnsupportedMediaType(HttpError):
    status = 415
    code = "unsupported_media_type"

    def __init__(self, received=None, expected=None):
        self.received = received
        self.expected = expected
        super().__init__("received %s, expected %s" % (received, expected))


class Invalid(HttpError):
    status = 422
    code = "invalid"

    def __init__(self, fields):
        self.fields = dict(fields)
        super().__init__("invalid: " + ", ".join(sorted(self.fields)))

    def as_dict(self):
        payload = super().as_dict()
        payload["fields"] = self.fields
        return payload
