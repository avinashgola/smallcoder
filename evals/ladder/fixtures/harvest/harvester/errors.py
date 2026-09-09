"""Errors raised while collecting results."""


class CollectError(Exception):
    """Something about the outcomes handed to the collector is wrong."""


class NotSealed(CollectError):
    """A summary was read before the collector finished with it."""

    def __init__(self, run_id):
        super().__init__("summary for %r has not been sealed yet" % (run_id,))
        self.run_id = run_id
