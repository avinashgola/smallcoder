"""A router using ``:name`` placeholders, e.g. ``/reports/:report_id``."""

from wire.urls import parts, tidy

from .errors import MethodNotAllowed, NotFound


class Entry:
    """One template bound to a handler."""

    def __init__(self, template, handler, methods=("GET",), name=None):
        self.template = tidy(template)
        self.handler = handler
        self.methods = frozenset(method.upper() for method in methods)
        self.name = name or self.template
        self.parts = parts(self.template)
        self.placeholders = [part[1:] for part in self.parts
                             if part.startswith(":")]

    def match(self, path):
        """Captured placeholders, or ``None``."""
        actual = parts(path)
        if len(actual) != len(self.parts):
            return None
        captured = {}
        for template_part, value in zip(self.parts, actual):
            if template_part.startswith(":"):
                if not value:
                    return None
                captured[template_part[1:]] = value
            elif template_part != value:
                return None
        return captured

    def __repr__(self):
        return "<Entry %s %s>" % ("|".join(sorted(self.methods)), self.template)


class Router:
    """Entries searched in registration order."""

    def __init__(self):
        self.entries = []

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def add(self, template, handler, methods=("GET",), name=None):
        entry = Entry(template, handler, methods, name)
        self.entries.append(entry)
        return entry

    def resolve(self, method, path):
        """Return ``(entry, captured)`` or raise an HTTP error."""
        method = method.upper()
        allowed = set()
        for entry in self.entries:
            captured = entry.match(path)
            if captured is None:
                continue
            if method not in entry.methods:
                allowed.update(entry.methods)
                continue
            return entry, captured
        if allowed:
            raise MethodNotAllowed(allowed)
        raise NotFound(tidy(path))

    def templates(self):
        return [entry.template for entry in self.entries]
