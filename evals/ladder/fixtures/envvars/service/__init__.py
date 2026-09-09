"""The report service: what it needs from the environment, and how it starts."""

from .bootstrap import configure, summary
from .spec import SERVICE_SPEC

__all__ = ["configure", "summary", "SERVICE_SPEC"]
