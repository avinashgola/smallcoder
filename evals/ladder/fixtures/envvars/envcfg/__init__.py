"""envcfg -- declare the settings a process needs, then read them.

A :class:`Spec` lists the settings; the loader pulls each one out of a mapping
that looks like ``os.environ`` and casts it to the declared type.
"""

from .errors import CastError, ConfigError, InvalidSetting, MissingSetting
from .loader import load
from .spec import Field, Spec

__all__ = [
    "CastError",
    "ConfigError",
    "InvalidSetting",
    "MissingSetting",
    "Field",
    "Spec",
    "load",
]
