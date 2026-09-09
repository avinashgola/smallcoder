"""Feature gating for the web application."""

from .flagset import REGISTRY
from .gate import active_features, can_use, why

__all__ = ["REGISTRY", "active_features", "can_use", "why"]
