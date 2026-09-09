"""Mutable bookkeeping for a single run."""

from flow.jobs import Status
from util.timing import Stopwatch


class JobRecord:
    """What happened to one job during one run."""

    __slots__ = ("job_id", "status", "duration", "detail", "started_at")

    def __init__(self, job_id):
        self.job_id = job_id
        self.status = Status.PENDING
        self.duration = 0.0
        self.detail = ""
        self.started_at = None

    def as_row(self):
        return (self.job_id, self.status, round(self.duration, 3), self.detail)

    def __repr__(self):
        return "JobRecord(%r, %s)" % (self.job_id, self.status)


class RunState:
    """Collects per job records and the overall wall clock of a run."""

    def __init__(self, run_id, clock):
        self.run_id = run_id
        self._clock = clock
        self._records = {}
        self._order = []
        self._watch = Stopwatch(clock)

    def begin(self):
        self._watch.start()
        return self

    def finish(self):
        return self._watch.stop()

    @property
    def elapsed(self):
        return self._watch.elapsed

    def record(self, job_id):
        if job_id not in self._records:
            self._records[job_id] = JobRecord(job_id)
            self._order.append(job_id)
        return self._records[job_id]

    def start_job(self, job_id):
        record = self.record(job_id)
        record.status = Status.RUNNING
        record.started_at = self._clock()
        return record

    def finish_job(self, job_id, status, detail=""):
        record = self.record(job_id)
        record.status = status
        record.detail = detail
        if record.started_at is not None:
            record.duration = round(self._clock() - record.started_at, 6)
        return record

    def mark(self, job_id, status, detail=""):
        record = self.record(job_id)
        record.status = status
        record.detail = detail
        return record

    def records(self):
        return [self._records[job_id] for job_id in self._order]

    def ids_with_status(self, status):
        return [r.job_id for r in self.records() if r.status == status]

    def counts(self):
        totals = {status: 0 for status in Status.ALL}
        for record in self.records():
            totals[record.status] += 1
        return totals
