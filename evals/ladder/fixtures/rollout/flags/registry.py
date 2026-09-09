"""A named collection of flags, and the flag-file format it is built from."""

from .errors import FlagDefinitionError, UnknownFlag
from .rules import Flag


class Registry:
    """Every flag the application knows about."""

    def __init__(self, flags=()):
        self._flags = {flag.name: flag for flag in flags}

    @classmethod
    def from_mapping(cls, definitions):
        """Build a registry from ``{name: {"percent": 25, ...}}``."""
        return cls(Flag.from_dict(name, dict(body)) for name, body in definitions.items())

    @classmethod
    def from_text(cls, text):
        """Build a registry from flag-file text."""
        return cls.from_mapping(parse_definitions(text))

    def __len__(self):
        return len(self._flags)

    def __contains__(self, name):
        return name in self._flags

    def names(self):
        """Flag names in a stable order."""
        return sorted(self._flags)

    def get(self, name):
        try:
            return self._flags[name]
        except KeyError:
            raise UnknownFlag(name) from None

    def is_on(self, name, subject):
        return self.get(name).decide(subject)

    def enabled_for(self, subject):
        """Names of the flags that are on for one subject."""
        return tuple(name for name in self.names() if self.is_on(name, subject))

    def rollout_plan(self):
        """``{name: percent}`` for the flags that are still being rolled out."""
        return {
            name: flag.percent
            for name, flag in sorted(self._flags.items())
            if flag.enabled and flag.percent < 100
        }


def parse_line(line):
    """Read one ``name: 50% allow=a,b`` definition line."""
    name, separator, rest = line.partition(":")
    name = name.strip()
    if not separator or not name:
        raise FlagDefinitionError(f"expected 'name: settings', got {line!r}")
    body = {}
    for token in rest.split():
        if token in ("on", "off"):
            body["enabled"] = token == "on"
        elif token.endswith("%"):
            body["percent"] = _percent(name, token)
        elif token.startswith(("allow=", "deny=")):
            key, _, listed = token.partition("=")
            body[key] = [item for item in listed.split(",") if item]
        else:
            raise FlagDefinitionError(f"{name}: cannot read {token!r}")
    return name, body


def parse_definitions(text):
    """Read a whole flag file into ``{name: body}``."""
    definitions = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, body = parse_line(line)
        if name in definitions:
            raise FlagDefinitionError(f"{name} is defined twice")
        definitions[name] = body
    return definitions


def _percent(name, token):
    try:
        return int(token[:-1])
    except ValueError:
        raise FlagDefinitionError(f"{name}: {token!r} is not a percentage") from None
