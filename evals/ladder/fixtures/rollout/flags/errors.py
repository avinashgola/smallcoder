"""Exceptions raised by the flag package."""


class FlagError(Exception):
    """Base class for every error raised here."""


class UnknownFlag(FlagError):
    """A flag was asked for by a name nothing defines."""

    def __init__(self, name):
        super().__init__(f"no flag named {name!r}")
        self.name = name


class FlagDefinitionError(FlagError):
    """A flag definition is not usable."""
