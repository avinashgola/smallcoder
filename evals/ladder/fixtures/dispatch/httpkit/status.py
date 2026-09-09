"""HTTP status codes and their reason phrases."""

PHRASES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    409: "Conflict",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}

_CLASS_PHRASES = {
    1: "Informational",
    2: "Success",
    3: "Redirection",
    4: "Client Error",
    5: "Server Error",
}


def phrase(code):
    """Reason phrase for ``code``, falling back to a phrase for its class."""
    if code in PHRASES:
        return PHRASES[code]
    return _CLASS_PHRASES.get(code // 100, "Unknown")


def status_line(code):
    """Render the status line fragment, e.g. ``404 Not Found``."""
    return "%d %s" % (code, phrase(code))


def is_success(code):
    return 200 <= code < 300


def is_redirect(code):
    return 300 <= code < 400


def is_client_error(code):
    return 400 <= code < 500


def is_error(code):
    return code >= 400


def allows_body(code):
    """Whether a response with this status is permitted to carry a body."""
    if 100 <= code < 200:
        return False
    return code not in (204, 304)
