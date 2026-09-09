"""Errors raised while configuring or running a pipeline."""


class PipelineError(Exception):
    """Base class for everything this project raises."""


class ConfigError(PipelineError):
    """A stage or plan was configured wrongly."""

    def __init__(self, message, where=None):
        super().__init__("%s (in %s)" % (message, where) if where else message)
        self.where = where


class StageError(PipelineError):
    """A stage failed while processing records."""

    def __init__(self, stage, message):
        super().__init__("stage %r failed: %s" % (stage, message))
        self.stage = stage
        self.message = message


class MissingField(StageError):
    """A record did not carry a field the stage needs."""

    def __init__(self, stage, field):
        super().__init__(stage, "record has no field %r" % (field,))
        self.field = field
