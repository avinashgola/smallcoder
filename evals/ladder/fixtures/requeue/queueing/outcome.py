"""Records describing what happened to a task."""

from support.fmt import attempt_label, seconds, truncate


class Outcome:
    """Terminal states a task can end in."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABANDONED = "abandoned"

    ALL = (SUCCEEDED, FAILED, ABANDONED)


class Attempt:
    """One execution of one task."""

    __slots__ = ("number", "ok", "error", "duration", "delay_before")

    def __init__(self, number, ok, error=None, duration=0.0, delay_before=0.0):
        self.number = int(number)
        self.ok = bool(ok)
        self.error = error
        self.duration = float(duration)
        self.delay_before = float(delay_before)

    def describe(self, total=None):
        state = "ok" if self.ok else "error: %s" % truncate(self.error, 48)
        return "%s %s in %s" % (
            attempt_label(self.number, total),
            state,
            seconds(self.duration),
        )

    def __repr__(self):
        return "Attempt(%d, %s)" % (self.number, "ok" if self.ok else "failed")


class TaskOutcome:
    """The full history of one task: every attempt plus the final state."""

    def __init__(self, task_id, status, attempts, value=None, error=None):
        self.task_id = task_id
        self.status = status
        self.attempts = list(attempts)
        self.value = value
        self.error = error

    @property
    def ok(self):
        return self.status == Outcome.SUCCEEDED

    @property
    def attempt_count(self):
        return len(self.attempts)

    @property
    def retries(self):
        """Executions beyond the first one."""
        return max(0, len(self.attempts) - 1)

    @property
    def total_delay(self):
        return round(sum(a.delay_before for a in self.attempts), 6)

    @property
    def total_duration(self):
        return round(sum(a.duration for a in self.attempts), 6)

    def describe(self):
        header = "task %s %s after %d attempt(s)" % (
            self.task_id,
            self.status,
            self.attempt_count,
        )
        lines = [header]
        for attempt in self.attempts:
            lines.append("  " + attempt.describe(len(self.attempts)))
        return "\n".join(lines)

    def __repr__(self):
        return "TaskOutcome(%r, %s, %d attempts)" % (
            self.task_id,
            self.status,
            self.attempt_count,
        )
