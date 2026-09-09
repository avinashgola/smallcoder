"""Stages: named callables that turn a list of rows into another list."""

from execution.errors import PlanError, StageFailure
from execution.outcome import State, StageOutcome


class Stage:
    """A named step. `fn(rows)` returns the rows the next stage receives."""

    def __init__(self, name, fn, critical=True):
        if not isinstance(name, str) or not name.strip():
            raise PlanError("stage name must be a non-empty string")
        if not callable(fn):
            raise PlanError("stage %r needs a callable body" % (name,))
        self.name = name.strip()
        self.fn = fn
        self.critical = bool(critical)

    def __call__(self, rows):
        return self.fn(rows)

    def describe(self):
        return "%s%s" % (self.name, "" if self.critical else " (optional)")

    def __repr__(self):
        return "Stage(%r)" % (self.name,)


def stage(name, critical=True):
    """Decorator turning a function into a `Stage`."""

    def wrap(fn):
        return Stage(name, fn, critical=critical)

    return wrap


def run_stage(step, rows, clock):
    """Run one stage over `rows`, returning `(rows_out, outcome)`.

    A failing stage passes its input through untouched so that the rest of the
    plan can still be attempted.
    """
    rows_in = list(rows)
    started = clock()
    try:
        produced = list(step(rows_in))
    except Exception as exc:
        duration = clock() - started
        if isinstance(exc, StageFailure):
            detail = exc.message
        else:
            detail = "%s: %s" % (type(exc).__name__, exc)
        outcome = StageOutcome(
            step.name,
            State.FAILED,
            rows_in=len(rows_in),
            rows_out=0,
            duration=duration,
            error=detail,
        )
        return rows_in, outcome
    duration = clock() - started
    outcome = StageOutcome(
        step.name,
        State.DONE,
        rows_in=len(rows_in),
        rows_out=len(produced),
        duration=duration,
    )
    return produced, outcome


def skipped_outcome(step, rows_in=0, reason="earlier stage failed"):
    return StageOutcome(
        step.name, State.SKIPPED, rows_in=rows_in, rows_out=0, error=reason
    )
