"""Converters turn one path segment into a typed value and back again."""


class ConversionError(ValueError):
    """Raised when a segment cannot be converted to the declared type."""


class Converter:
    """Base class: matches exactly one segment unless ``greedy`` is set."""

    name = "str"
    greedy = False

    def to_python(self, segment):
        return segment

    def to_url(self, value):
        return str(value)

    def __repr__(self):
        return "<%s>" % self.name


class StringConverter(Converter):
    name = "str"

    def to_python(self, segment):
        if not segment:
            raise ConversionError("empty segment")
        return segment


class IntConverter(Converter):
    name = "int"

    def to_python(self, segment):
        if not segment.isdigit():
            raise ConversionError("%r is not an integer" % (segment,))
        return int(segment)

    def to_url(self, value):
        return str(int(value))


class SlugConverter(Converter):
    name = "slug"
    _allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")

    def to_python(self, segment):
        if not segment or not set(segment) <= self._allowed:
            raise ConversionError("%r is not a slug" % (segment,))
        return segment


class UuidConverter(Converter):
    name = "uuid"
    _sizes = (8, 4, 4, 4, 12)
    _hex = set("0123456789abcdef")

    def to_python(self, segment):
        parts = segment.lower().split("-")
        if len(parts) != len(self._sizes):
            raise ConversionError("%r is not a uuid" % (segment,))
        for part, size in zip(parts, self._sizes):
            if len(part) != size or not set(part) <= self._hex:
                raise ConversionError("%r is not a uuid" % (segment,))
        return segment.lower()


class PathConverter(Converter):
    """Matches the remaining segments, slashes included."""

    name = "path"
    greedy = True

    def to_python(self, segment):
        return segment.strip("/")


REGISTRY = {
    "str": StringConverter(),
    "int": IntConverter(),
    "slug": SlugConverter(),
    "uuid": UuidConverter(),
    "path": PathConverter(),
}


def get_converter(name):
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError("unknown converter %r" % (name,)) from None
