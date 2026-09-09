"""Exceptions that the application renders as HTTP responses."""


class HttpError(Exception):
    """Base class for failures that have a natural status code."""

    status = 500
    title = "Internal Server Error"

    def __init__(self, detail=None, headers=None):
        super().__init__(detail or self.title)
        self.detail = detail or self.title
        self.headers = dict(headers or {})

    def payload(self):
        return {"error": self.title, "detail": self.detail, "status": self.status}


class BadRequest(HttpError):
    status = 400
    title = "Bad Request"


class Unauthorized(HttpError):
    status = 401
    title = "Unauthorized"

    def __init__(self, detail=None, realm="api"):
        headers = {"WWW-Authenticate": 'Bearer realm="%s"' % realm}
        super().__init__(detail, headers)
        self.realm = realm


class Forbidden(HttpError):
    status = 403
    title = "Forbidden"


class NotFound(HttpError):
    status = 404
    title = "Not Found"

    def __init__(self, path=None):
        self.path = path
        detail = "no route for %s" % path if path else None
        super().__init__(detail)


class MethodNotAllowed(HttpError):
    """Raised when a path exists but not for the method that was used."""

    status = 405
    title = "Method Not Allowed"

    def __init__(self, allowed):
        self.allowed = list(allowed)
        joined = ", ".join(self.allowed)
        super().__init__("allowed methods: " + joined, {"Allow": joined})


class Conflict(HttpError):
    status = 409
    title = "Conflict"


class PayloadTooLarge(HttpError):
    status = 413
    title = "Payload Too Large"

    def __init__(self, limit):
        self.limit = limit
        super().__init__("body exceeds %d bytes" % limit)


class UnsupportedMediaType(HttpError):
    status = 415
    title = "Unsupported Media Type"

    def __init__(self, received=None, expected=None):
        detail = None
        if received or expected:
            detail = "got %s, expected %s" % (received or "nothing", expected or "?")
        super().__init__(detail)


class ValidationError(HttpError):
    status = 422
    title = "Unprocessable Entity"

    def __init__(self, fields):
        self.fields = dict(fields)
        super().__init__("invalid fields: " + ", ".join(sorted(self.fields)))

    def payload(self):
        data = super().payload()
        data["fields"] = self.fields
        return data
