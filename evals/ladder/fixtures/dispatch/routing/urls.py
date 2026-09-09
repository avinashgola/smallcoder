"""Reverse URL construction from route names."""

from httpkit.query import unquote


def quote_segment(text):
    """Percent-encode the characters that may not appear in a path segment."""
    safe = "-._~"
    out = []
    for char in str(text):
        if char.isalnum() or char in safe:
            out.append(char)
        else:
            out.extend("%%%02X" % byte for byte in char.encode("utf-8"))
    return "".join(out)


def encode_query(pairs):
    """Build a query string from ``(name, value)`` pairs."""
    if not pairs:
        return ""
    if hasattr(pairs, "items"):
        pairs = sorted(pairs.items())
    chunks = ["%s=%s" % (quote_segment(name), quote_segment(value))
              for name, value in pairs]
    return "?" + "&".join(chunks)


class UrlBuilder:
    """Builds URLs for named routes, the inverse of the router's matching."""

    def __init__(self, router, script_name=""):
        self.router = router
        self.script_name = script_name.rstrip("/")

    def url_for(self, name, query=None, **values):
        route = self.router.get(name)
        path = route.build(**values)
        segments = [quote_segment(unquote(part)) for part in path.split("/") if part]
        rendered = "/" + "/".join(segments) if segments else "/"
        return self.script_name + rendered + encode_query(query)
