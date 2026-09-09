"""A small route table using ``{name}`` placeholders."""

from message.urls import normalize, segments

from .errors import MethodNotAllowed, NotFound

CASTS = {
    "int": int,
    "str": str,
}


def _cast(kind, raw):
    caster = CASTS.get(kind)
    if caster is None:
        raise ValueError("unknown placeholder type %r" % (kind,))
    return caster(raw)


class Rule:
    """One template bound to an endpoint and a set of methods."""

    def __init__(self, template, endpoint, methods=("GET",), name=None):
        self.template = normalize(template)
        self.endpoint = endpoint
        self.methods = frozenset(method.upper() for method in methods)
        self.name = name or getattr(endpoint, "__name__", self.template)
        self.parts = segments(self.template)

    def match(self, path):
        """Captured placeholders, or ``None`` when the path does not fit."""
        parts = segments(path)
        if len(parts) != len(self.parts):
            return None
        captured = {}
        for template_part, actual in zip(self.parts, parts):
            if template_part.startswith("{") and template_part.endswith("}"):
                inner = template_part[1:-1]
                kind, _, name = inner.partition(":") if ":" in inner else ("str", "", inner)
                try:
                    captured[name] = _cast(kind, actual)
                except ValueError:
                    return None
            elif template_part != actual:
                return None
        return captured

    def accepts(self, method):
        return method.upper() in self.methods

    def __repr__(self):
        return "<Rule %s %s>" % ("|".join(sorted(self.methods)), self.template)


class RouteTable:
    """Ordered rules, searched from the top."""

    def __init__(self):
        self.rules = []

    def __len__(self):
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def add(self, template, endpoint, methods=("GET",), name=None):
        rule = Rule(template, endpoint, methods, name)
        self.rules.append(rule)
        return rule

    def find(self, method, path):
        """Return ``(rule, params)`` or raise the matching HTTP error."""
        allowed = set()
        for rule in self.rules:
            params = rule.match(path)
            if params is None:
                continue
            if not rule.accepts(method):
                allowed.update(rule.methods)
                continue
            return rule, params
        if allowed:
            raise MethodNotAllowed(allowed)
        raise NotFound(normalize(path))

    def named(self, name):
        for rule in self.rules:
            if rule.name == name:
                return rule
        raise KeyError(name)

    def describe(self):
        return [repr(rule) for rule in self.rules]
