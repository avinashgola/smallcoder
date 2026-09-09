"""Result objects produced by a run."""

from flow.jobs import Status
from util.tabular import render_table
from util.text import plural
from util.timing import format_seconds


class JobResult:
    """The outcome of a single job."""

    __slots__ = ("job_id", "status", "value", "detail", "duration")

    def __init__(self, job_id, status, value=None, detail="", duration=0.0):
        self.job_id = job_id
        self.status = status
        self.value = value
        self.detail = detail
        self.duration = float(duration)

    @property
    def ok(self):
        return self.status == Status.SUCCEEDED

    def as_row(self):
        return (
            self.job_id,
            self.status,
            format_seconds(self.duration),
            self.detail,
        )

    def __repr__(self):
        return "JobResult(%r, %s)" % (self.job_id, self.status)


class RunReport:
    """Everything a caller needs to know about a finished run."""

    HEADERS = ("job", "status", "time", "detail")

    def __init__(self, run_id, results, order, elapsed):
        self.run_id = run_id
        self.results = list(results)
        self.order = list(order)
        self.elapsed = float(elapsed)

    def by_id(self):
        return {result.job_id: result for result in self.results}

    def values(self):
        """Return values of every job that succeeded, keyed by job id."""
        return {r.job_id: r.value for r in self.results if r.ok}

    def with_status(self, status):
        return [r.job_id for r in self.results if r.status == status]

    @property
    def succeeded(self):
        return self.with_status(Status.SUCCEEDED)

    @property
    def failed(self):
        return self.with_status(Status.FAILED)

    @property
    def skipped(self):
        return self.with_status(Status.SKIPPED)

    @property
    def ok(self):
        return not self.failed

    def summary_line(self):
        return "run %s: %s succeeded, %s failed, %s skipped in %s" % (
            self.run_id,
            len(self.succeeded),
            len(self.failed),
            len(self.skipped),
            format_seconds(self.elapsed),
        )

    def table(self):
        return render_table([r.as_row() for r in self.results], self.HEADERS)

    def describe(self):
        return "%s\n%s" % (self.summary_line(), self.table())

    def __len__(self):
        return len(self.results)

    def __repr__(self):
        return "RunReport(%r, %s)" % (self.run_id, plural(len(self.results), "result"))
