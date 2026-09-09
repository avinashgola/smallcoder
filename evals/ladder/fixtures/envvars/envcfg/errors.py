"""Exceptions raised while reading settings."""


class ConfigError(Exception):
    """Base class for every error in this package."""


class MissingSetting(ConfigError):
    """A required variable is not set."""

    def __init__(self, variable):
        super().__init__(f"{variable} is required but not set")
        self.variable = variable


class CastError(ConfigError):
    """A variable is set but cannot be read as the declared type."""

    def __init__(self, kind, raw, where=None):
        target = where or "value"
        super().__init__(f"{target}: {raw!r} is not a valid {kind}")
        self.kind = kind
        self.raw = raw
        self.where = where


class InvalidSetting(ConfigError):
    """A value is well formed but not one of the allowed choices."""

    def __init__(self, name, value, allowed):
        allowed_text = ", ".join(str(item) for item in allowed)
        super().__init__(f"{name}={value!r} is not one of: {allowed_text}")
        self.name = name
        self.value = value
        self.allowed = tuple(allowed)
