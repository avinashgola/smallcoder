"""Compilation of route templates such as ``/posts/<int:post_id>``."""

from .converters import ConversionError, get_converter

STATIC = "static"
DYNAMIC = "dynamic"


def normalize_path(path):
    """Give ``path`` a leading slash and drop a trailing one."""
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def split_path(path):
    """The non-empty segments of ``path``."""
    return [segment for segment in normalize_path(path).split("/") if segment]


def _parse_placeholder(token):
    """``<int:post_id>`` -> ``("post_id", IntConverter())``."""
    inner = token[1:-1].strip()
    if not inner:
        raise ValueError("empty placeholder")
    if ":" in inner:
        kind, _, name = inner.partition(":")
    else:
        kind, name = "str", inner
    if not name:
        raise ValueError("placeholder %r has no name" % (token,))
    return name, get_converter(kind.strip())


class Segment:
    """One compiled piece of a route template."""

    def __init__(self, kind, text, name=None, converter=None):
        self.kind = kind
        self.text = text
        self.name = name
        self.converter = converter

    @property
    def greedy(self):
        return self.converter is not None and self.converter.greedy

    def __repr__(self):
        return "Segment(%s, %r)" % (self.kind, self.text)


class Pattern:
    """A compiled route template that can match paths and build URLs."""

    def __init__(self, template):
        self.template = normalize_path(template)
        self.segments = []
        for token in split_path(self.template):
            if token.startswith("<") and token.endswith(">"):
                name, converter = _parse_placeholder(token)
                self.segments.append(Segment(DYNAMIC, token, name, converter))
            else:
                self.segments.append(Segment(STATIC, token))
        greedy = [index for index, seg in enumerate(self.segments) if seg.greedy]
        if greedy and greedy[0] != len(self.segments) - 1:
            raise ValueError("a greedy placeholder must come last")
        self.greedy = bool(greedy)

    @property
    def parameter_names(self):
        return [seg.name for seg in self.segments if seg.kind == DYNAMIC]

    @property
    def weight(self):
        """Static segments sort ahead of dynamic ones when routes overlap."""
        return sum(2 if seg.kind == STATIC else 1 for seg in self.segments)

    def match(self, path):
        """Return the captured parameters, or ``None`` when ``path`` differs."""
        parts = split_path(path)
        if self.greedy:
            if len(parts) < len(self.segments):
                return None
        elif len(parts) != len(self.segments):
            return None
        captured = {}
        for index, segment in enumerate(self.segments):
            if segment.greedy:
                rest = "/".join(parts[index:])
                captured[segment.name] = segment.converter.to_python(rest)
                return captured
            part = parts[index]
            if segment.kind == STATIC:
                if part != segment.text:
                    return None
                continue
            try:
                captured[segment.name] = segment.converter.to_python(part)
            except ConversionError:
                return None
        return captured

    def build(self, values):
        """Render the template with ``values`` substituted in."""
        parts = []
        for segment in self.segments:
            if segment.kind == STATIC:
                parts.append(segment.text)
                continue
            if segment.name not in values:
                raise KeyError("missing parameter %r" % (segment.name,))
            parts.append(segment.converter.to_url(values[segment.name]))
        return "/" + "/".join(parts) if parts else "/"

    def __repr__(self):
        return "Pattern(%r)" % (self.template,)
