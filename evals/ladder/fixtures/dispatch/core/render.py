"""Turn whatever a view returned into a Response object."""

from httpkit.response import JsonResponse, Response


def coerce_response(result):
    """Accept the several shapes a view is allowed to return."""
    if isinstance(result, Response):
        return result
    if result is None:
        return Response(b"", 204)
    if isinstance(result, tuple):
        if len(result) == 2:
            body, status = result
            return coerce_body(body, status)
        raise TypeError("a view tuple must be (body, status)")
    return coerce_body(result, 200)


def coerce_body(body, status):
    if isinstance(body, Response):
        body.status = status
        return body
    if isinstance(body, (dict, list)):
        return JsonResponse(body, status)
    if isinstance(body, (str, bytes)):
        return Response(body, status)
    raise TypeError("cannot render %r as a response" % (type(body).__name__,))
