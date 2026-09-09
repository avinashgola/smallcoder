"""Exception hierarchy for the pipeline."""


class FlowError(Exception):
    """Base class for every error this package raises."""


class GraphError(FlowError):
    """The dependency graph is malformed (unknown job, self edge, cycle)."""


class ScheduleError(FlowError):
    """The scheduler cannot make progress."""

    def __init__(self, message, blocked=()):
        super().__init__(message)
        self.blocked = tuple(blocked)


class SpecError(FlowError):
    """A pipeline specification is invalid."""

    def __init__(self, message, path=()):
        location = ".".join(str(part) for part in path)
        super().__init__("%s (at %s)" % (message, location) if location else message)
        self.path = tuple(path)


class JobFailed(FlowError):
    """Raised by an action to signal a normal, reportable job failure."""

    def __init__(self, job_id, message):
        super().__init__("job %s failed: %s" % (job_id, message))
        self.job_id = job_id
        self.message = message
