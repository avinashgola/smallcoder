"""Status codes used by the server."""

OK = 200
CREATED = 201
NO_CONTENT = 204
NOT_MODIFIED = 304
BAD_REQUEST = 400
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
NOT_ACCEPTABLE = 406
UNSUPPORTED_MEDIA_TYPE = 415
SERVER_ERROR = 500

REASONS = {
    OK: "OK",
    CREATED: "Created",
    NO_CONTENT: "No Content",
    NOT_MODIFIED: "Not Modified",
    BAD_REQUEST: "Bad Request",
    NOT_FOUND: "Not Found",
    METHOD_NOT_ALLOWED: "Method Not Allowed",
    NOT_ACCEPTABLE: "Not Acceptable",
    UNSUPPORTED_MEDIA_TYPE: "Unsupported Media Type",
    SERVER_ERROR: "Internal Server Error",
}


def reason(code):
    return REASONS.get(code, "Unknown")


def bodyless(code):
    return code in (NO_CONTENT, NOT_MODIFIED) or 100 <= code < 200
