"""What one stage did during one run."""

from toolkit.timing import format_duration, rate_per_second


class State:
    """Terminal states a stage can end in."""

    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"

    ALL = (DONE, FAILED, SKIPPED)


class StageOutcome:
    """An immutable record of one stage's pass over the rows."""

    __slots__ = ("stage", "state", "rows_in", "rows_out", "duration", "error",
                 "warnings")

    def __init__(self, stage, state, rows_in=0, rows_out=0, duration=0.0,
                 error=None, warnings=()):
        if state not in State.ALL:
            raise ValueError("unknown stage state %r" % (state,))
        self.stage = stage
        self.state = state
        self.rows_in = int(rows_in)
        self.rows_out = int(rows_out)
        self.duration = float(duration)
        self.error = error
        self.warnings = tuple(warnings)

    # -- predicates ------------------------------------------------------

    @property
    def ok(self):
        return self.state == State.DONE

    @property
    def failed(self):
        return self.state == State.FAILED

    @property
    def skipped(self):
        return self.state == State.SKIPPED

    @property
    def dropped(self):
        return max(0, self.rows_in - self.rows_out)

    @property
    def rows_per_second(self):
        return rate_per_second(self.rows_out, self.duration)

    # -- rendering -------------------------------------------------------

    def as_row(self):
        return (
            self.stage,
            self.state,
            self.rows_in,
            self.rows_out,
            format_duration(self.duration),
        )

    def to_dict(self):
        return {
            "stage": self.stage,
            "state": self.state,
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "duration": round(self.duration, 6),
            "error": self.error,
            "warnings": list(self.warnings),
        }

    def describe(self):
        text = "%s %s: %d -> %d rows in %s" % (
            self.stage,
            self.state,
            self.rows_in,
            self.rows_out,
            format_duration(self.duration),
        )
        if self.error:
            text += " (%s)" % self.error
        return text

    def __repr__(self):
        return "StageOutcome(%r, %s)" % (self.stage, self.state)
