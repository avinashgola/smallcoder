"""Building the outward-facing URL of a named route.

A route only knows the path inside its own application, so anything that
hands a URL back to a client has to put the prefixes the request travelled
through back on the front of it.
"""

from mounting.prefix import join

SAFE = "-._~"


def quote(text):
    """Percent-encode everything that may not appear in a path segment."""
    out = []
    for char in str(text):
        if char.isalnum() or char in SAFE:
            out.append(char)
        else:
            out.extend("%%%02X" % byte for byte in char.encode("utf-8"))
    return "".join(out)


def encode_query(query):
    """Render ``{"a": 1}`` or ``[("a", 1)]`` as ``?a=1``."""
    if not query:
        return ""
    pairs = sorted(query.items()) if hasattr(query, "items") else list(query)
    return "?" + "&".join("%s=%s" % (quote(name), quote(value))
                          for name, value in pairs)


def url_for(app, name, values=None, query=None, script_name=""):
    """The URL of route ``name`` in ``app``, as a client should see it.

    ``script_name`` is the prefix the current request already travelled
    through; pass ``request.script_name`` when answering a request.
    """
    route = app.router.named(name)
    path = route.build(**(values or {}))
    return join(script_name, path) + encode_query(query)


def path_of(app, name, values=None):
    """The inner path of a named route, without any mount prefix."""
    return app.router.named(name).build(**(values or {}))
