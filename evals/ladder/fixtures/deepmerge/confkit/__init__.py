"""confkit -- small layered configuration toolkit.

A configuration is an ordinary nested mapping.  Layers are stacked lowest
priority first (packaged defaults, then a file, then command-line overrides)
and resolved into a single mapping.
"""

from .errors import ConfigError, InvalidLayer, MissingKey, ParseError
from .layers import Layer, LayerStack
from .merge import diff, merge, merge_all, prune

__all__ = [
    "ConfigError",
    "InvalidLayer",
    "MissingKey",
    "ParseError",
    "Layer",
    "LayerStack",
    "diff",
    "merge",
    "merge_all",
    "prune",
]
