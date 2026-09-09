"""Exception types raised by confkit."""


class ConfigError(Exception):
    """Base class for every error this package raises."""


class MissingKey(ConfigError):
    """A dotted key was requested but no layer provides it."""

    def __init__(self, path):
        super().__init__(f"no value for {path!r}")
        self.path = path


class InvalidLayer(ConfigError):
    """A layer was added with something other than a mapping."""


class ParseError(ConfigError):
    """A configuration file could not be read."""

    def __init__(self, line_number, message):
        super().__init__(f"line {line_number}: {message}")
        self.line_number = line_number
