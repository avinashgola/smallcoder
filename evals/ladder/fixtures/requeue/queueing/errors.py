"""Errors raised by the queue, and the two error kinds handlers should raise."""


class QueueError(Exception):
    """Base class for queue infrastructure problems."""


class UnknownTask(QueueError):
    def __init__(self, task_id):
        super().__init__("no task with id %r" % (task_id,))
        self.task_id = task_id


class TransientError(Exception):
    """A handler failure that is worth retrying (timeouts, 503s, locks)."""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class PermanentError(Exception):
    """A handler failure that will never succeed (bad payload, 404)."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class RetriesExhausted(Exception):
    """Raised when a caller asks for a value from a task that never succeeded."""

    def __init__(self, task_id, attempts):
        super().__init__("task %r gave up after %d attempts" % (task_id, attempts))
        self.task_id = task_id
        self.attempts = attempts
