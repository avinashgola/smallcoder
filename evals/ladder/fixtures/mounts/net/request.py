"""The request object.

The request target is used exactly as the client sent it: nothing here
re-roots a path, because a mounted application is served a path that has
already been rewritten for it.
"""

import json

from .headers import Headers


def clean(path):
    """Collapse repeated slashes and drop a trailing one."""
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def parse_query(raw):
    if not raw:
        return []
    raw = raw[1:] if raw.startswith("?") else raw
    pairs = []
    for chunk in raw.split("&"):
        if not chunk:
            continue
        name, _, value = chunk.partition("=")
        pairs.append((name.replace("+", " "), value.replace("+", " ")))
    return pairs


class Request:
    """One inbound request plus the bookkeeping mounting needs."""

    def __init__(self, method="GET", path="/", headers=None, query="", body=b"",
                 script_name=""):
        self.method = method.upper()
        self.path = clean(path)
        self.headers = headers if isinstance(headers, Headers) else Headers(headers)
        self.query_string = query[1:] if query.startswith("?") else query
        self.body = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.args = parse_query(self.query_string)
        self.vars = {}
        self.notes = {}
        self.script_name = script_name

    @property
    def full_path(self):
        """The path as the outermost client asked for it."""
        return clean(self.script_name + self.path) if self.script_name else self.path

    def arg(self, name, default=None):
        for key, value in self.args:
            if key == name:
                return value
        return default

    def var(self, name, default=None):
        return self.vars.get(name, default)

    def json(self):
        if not self.body:
            return None
        return json.loads(self.body.decode("utf-8"))

    def relocate(self, path, consumed=""):
        """A copy pointing at ``path``, remembering the prefix taken off.

        The new path is used verbatim; whoever calls this is responsible for
        handing over something the receiving router can match.
        """
        clone = Request(self.method, path, self.headers.copy(),
                        self.query_string, self.body,
                        self.script_name + consumed)
        clone.notes = self.notes
        return clone

    def __repr__(self):
        return "<Request %s %s>" % (self.method, self.path)
