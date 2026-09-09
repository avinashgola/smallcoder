"""Stage protocol, per-run context, results and the stage registry."""

from stages.base import Stage
from stages.context import StageContext
from stages.registry import StageRegistry
from stages.result import StageResult

__all__ = ["Stage", "StageContext", "StageRegistry", "StageResult"]
