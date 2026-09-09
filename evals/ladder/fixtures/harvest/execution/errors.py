"""Errors raised while executing a plan."""


class ExecutionError(Exception):
    """Base class for execution problems."""


class StageFailure(ExecutionError):
    """Raised by a stage body to report a normal, recoverable failure."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class PlanError(ExecutionError):
    """The plan itself is unusable (no stages, duplicate names)."""
