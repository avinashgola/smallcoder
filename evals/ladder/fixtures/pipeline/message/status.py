"""Status code helpers."""

REASONS = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    409: "Conflict",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

EMPTY_BODY = frozenset([204, 304])


def reason(code):
    if code in REASONS:
        return REASONS[code]
    if code // 100 == 2:
        return "Success"
    if code // 100 == 4:
        return "Client Error"
    if code // 100 == 5:
        return "Server Error"
    return "Unknown"


def ok(code):
    return 200 <= code < 400


def failed(code):
    return code >= 400


def may_have_body(code):
    return code not in EMPTY_BODY and not 100 <= code < 200
