"""Assemble the effective settings for a run of the service."""

from confkit import LayerStack
from confkit.errors import MissingKey
from confkit.inifile import parse
from confkit.merge import prune
from confkit.paths import expand, flatten

from .defaults import DEFAULTS, REQUIRED_PATHS


def build_stack(profile_text=None, cli=None):
    """Stack the three layers: defaults, then a profile file, then the CLI.

    ``cli`` is a flat mapping of dotted paths, the way a ``--set a.b=1`` flag
    would hand them over.
    """
    stack = LayerStack().add("defaults", DEFAULTS)
    if profile_text is not None:
        stack.add("profile", parse(profile_text))
    if cli:
        stack.add("cli", expand(cli))
    return stack


def resolve(profile_text=None, cli=None):
    """Return the effective settings mapping."""
    settings = build_stack(profile_text, cli).resolve()
    check_required(settings)
    return settings


def check_required(settings):
    """Raise :class:`MissingKey` if a mandatory path did not survive."""
    flat = flatten(settings)
    for path in REQUIRED_PATHS:
        if path not in flat:
            raise MissingKey(path)


def origins(profile_text=None, cli=None):
    """Map every effective dotted path to the layer that supplied it."""
    stack = build_stack(profile_text, cli)
    settings = prune(stack.resolve())
    return {path: stack.origin(path) for path in flatten(settings)}
