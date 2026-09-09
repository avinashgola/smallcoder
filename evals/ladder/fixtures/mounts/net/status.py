"""Status codes and the small predicates the response object needs."""

REASONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


def reason(code):
    if code in REASONS:
        return REASONS[code]
    return {2: "Success", 3: "Redirection", 4: "Client Error",
            5: "Server Error"}.get(code // 100, "Unknown")


def is_redirect(code):
    return code in (301, 302, 303, 307, 308)


def has_body(code):
    return code not in (204, 304) and not 100 <= code < 200
