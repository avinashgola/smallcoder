"""HTTP errors."""

from wire import status


class HttpError(Exception):
    """An error that the server knows how to answer with."""

    status = status.SERVER_ERROR
    slug = "server_error"

    def __init__(self, detail=None, headers=None):
        super().__init__(detail or self.slug)
        self.detail = detail
        self.headers = dict(headers or {})

    def body(self):
        payload = {"error": self.slug, "status": self.status}
        if self.detail:
            payload["detail"] = self.detail
        return payload


class BadRequest(HttpError):
    status = status.BAD_REQUEST
    slug = "bad_request"


class NotFound(HttpError):
    status = status.NOT_FOUND
    slug = "not_found"

    def __init__(self, path=None):
        self.path = path
        super().__init__("nothing at %s" % path if path else None)


class MethodNotAllowed(HttpError):
    status = status.METHOD_NOT_ALLOWED
    slug = "method_not_allowed"

    def __init__(self, allowed):
        self.allowed = sorted(allowed)
        joined = ", ".join(self.allowed)
        super().__init__("allowed: " + joined, {"Allow": joined})


class NotAcceptable(HttpError):
    """Raised when nothing the server can produce is acceptable."""

    status = status.NOT_ACCEPTABLE
    slug = "not_acceptable"

    def __init__(self, offers):
        self.offers = list(offers)
        super().__init__("this resource can only serve: "
                         + ", ".join(self.offers))

    def body(self):
        payload = super().body()
        payload["available"] = self.offers
        return payload


class UnsupportedMediaType(HttpError):
    status = status.UNSUPPORTED_MEDIA_TYPE
    slug = "unsupported_media_type"
