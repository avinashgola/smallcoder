"""Turn the environment into the values the service actually runs with."""

from envcfg.loader import load
from envcfg.report import describe, missing_variables

from .spec import SERVICE_SPEC


def configure(environ, **overrides):
    """Effective configuration for one process.

    Keyword arguments stand in for command-line flags and win over the
    environment.
    """
    values = load(environ, SERVICE_SPEC, overrides)
    values["bind"] = f"{values['host']}:{values['port']}"
    return values


def summary(values):
    """Lines suitable for the start-up banner, with secrets masked."""
    return describe(SERVICE_SPEC, values)


def preflight(environ):
    """Variables that must be set before the service can start."""
    return missing_variables(environ, SERVICE_SPEC)
