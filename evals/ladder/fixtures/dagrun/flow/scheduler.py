"""Turns a dependency graph into an execution order.

The scheduler keeps, for every job, how many upstream jobs it is still waiting
for. A job becomes runnable when that counter reaches zero; finishing a job
decrements the counter of everything downstream of it.
"""

from flow.errors import ScheduleError
from flow.jobs import Status


class Scheduler:
    """Hands out runnable jobs and tracks what is still outstanding."""

    def __init__(self, graph):
        graph.validate()
        self._graph = graph
        self._status = {}
        self._waiting_on = {}
        for job_id in graph.job_ids():
            self._status[job_id] = Status.PENDING
            self._waiting_on[job_id] = len(graph.dependencies_of(job_id))

    # -- inspection ------------------------------------------------------

    @property
    def graph(self):
        return self._graph

    def status_of(self, job_id):
        return self._status[job_id]

    def statuses(self):
        return dict(self._status)

    def waiting_on(self, job_id):
        """How many upstream jobs this job is still blocked by."""
        return self._waiting_on[job_id]

    def remaining(self):
        """Jobs that have not reached a terminal status yet."""
        return [
            job_id
            for job_id in self._graph.job_ids()
            if self._status[job_id] not in Status.TERMINAL
        ]

    def is_done(self):
        return not self.remaining()

    # -- handing out work ------------------------------------------------

    def ready(self):
        """Pending jobs whose dependencies have all succeeded."""
        return [
            job_id
            for job_id in self._graph.job_ids()
            if self._status[job_id] == Status.PENDING and self._waiting_on[job_id] == 0
        ]

    def take(self, limit=None):
        """Claim up to `limit` runnable jobs, marking them as running."""
        claimed = self.ready()
        if limit is not None:
            claimed = claimed[:limit]
        if not claimed and self.remaining():
            raise ScheduleError(
                "no runnable jobs but %d still pending" % len(self.remaining()),
                blocked=self.remaining(),
            )
        for job_id in claimed:
            self._status[job_id] = Status.RUNNING
        return claimed

    # -- reporting results ----------------------------------------------

    def mark_succeeded(self, job_id):
        """Record success and return the jobs that just became runnable."""
        self._transition(job_id, Status.SUCCEEDED)
        unblocked = []
        for child in self._graph.dependents_of(job_id):
            self._waiting_on[child] -= 1
            if self._waiting_on[child] == 0 and self._status[child] == Status.PENDING:
                unblocked.append(child)
        return unblocked

    def mark_failed(self, job_id):
        """Record failure and skip everything downstream. Returns the skipped."""
        self._transition(job_id, Status.FAILED)
        skipped = []
        for child in self._graph.descendants_of(job_id):
            if self._status[child] in Status.TERMINAL:
                continue
            self._status[child] = Status.SKIPPED
            skipped.append(child)
        return skipped

    def mark_skipped(self, job_id):
        """Skip a job on purpose; downstream jobs are skipped too."""
        self._transition(job_id, Status.SKIPPED)
        skipped = []
        for child in self._graph.descendants_of(job_id):
            if self._status[child] in Status.TERMINAL:
                continue
            self._status[child] = Status.SKIPPED
            skipped.append(child)
        return skipped

    def _transition(self, job_id, status):
        current = self._status[job_id]
        if current in Status.TERMINAL:
            raise ScheduleError(
                "job %r is already %s, cannot mark %s" % (job_id, current, status)
            )
        self._status[job_id] = status

    # -- static ordering -------------------------------------------------

    def waves(self):
        """Group the whole graph into successive batches of parallel jobs."""
        pending = dict(self._waiting_on)
        done = set()
        batches = []
        while len(done) < len(self._graph):
            batch = [
                job_id
                for job_id in self._graph.job_ids()
                if job_id not in done and pending[job_id] == 0
            ]
            if not batch:
                raise ScheduleError(
                    "cannot order the remaining jobs",
                    blocked=[j for j in self._graph.job_ids() if j not in done],
                )
            for job_id in batch:
                done.add(job_id)
                for child in self._graph.dependents_of(job_id):
                    pending[child] -= 1
            batches.append(batch)
        return batches

    def linear_order(self):
        """Flatten `waves` into a single valid execution order."""
        order = []
        for batch in self.waves():
            order.extend(batch)
        return order
