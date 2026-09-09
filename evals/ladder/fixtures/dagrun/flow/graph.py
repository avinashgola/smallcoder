"""The dependency graph.

Jobs are nodes; an edge from A to B means "B must not start before A has
finished". Two indexes are kept: `_deps` maps a job to the jobs it waits for,
in declaration order, and `_dependents` maps a job to the jobs waiting on it.
The scheduler reads both, so they are always written together.
"""

from flow.errors import GraphError
from flow.jobs import Job
from util.sets import ordered_unique


class DependencyGraph:
    """A mutable DAG of jobs with insertion ordered iteration."""

    def __init__(self):
        self._jobs = {}
        self._deps = {}
        self._dependents = {}
        self._order = []

    # -- construction ----------------------------------------------------

    def add_job(self, job):
        """Register a job. Adding the same id twice is an error."""
        if not isinstance(job, Job):
            raise GraphError("expected a Job, got %r" % (type(job).__name__,))
        if job.id in self._jobs:
            raise GraphError("duplicate job id %r" % (job.id,))
        self._jobs[job.id] = job
        self._deps[job.id] = []
        self._dependents[job.id] = set()
        self._order.append(job.id)
        return job

    def add_dependency(self, job_id, depends_on):
        """Record that `job_id` waits for `depends_on`."""
        self._require(job_id)
        self._require(depends_on)
        if job_id == depends_on:
            raise GraphError("job %r cannot depend on itself" % (job_id,))
        self._deps[job_id].append(depends_on)
        self._dependents[depends_on].add(job_id)

    def _require(self, job_id):
        if job_id not in self._jobs:
            raise GraphError("unknown job %r" % (job_id,))

    # -- queries ---------------------------------------------------------

    def __contains__(self, job_id):
        return job_id in self._jobs

    def __len__(self):
        return len(self._jobs)

    def __iter__(self):
        return iter(self.job_ids())

    def job(self, job_id):
        self._require(job_id)
        return self._jobs[job_id]

    def job_ids(self):
        """Ids in declaration order."""
        return list(self._order)

    def jobs(self):
        return [self._jobs[job_id] for job_id in self._order]

    def dependencies_of(self, job_id):
        """Jobs `job_id` waits for, in the order they were declared."""
        self._require(job_id)
        return list(self._deps[job_id])

    def dependents_of(self, job_id):
        """Jobs that wait for `job_id`, in declaration order."""
        self._require(job_id)
        waiting = self._dependents[job_id]
        return [other for other in self._order if other in waiting]

    def roots(self):
        """Jobs with no dependencies at all."""
        return [job_id for job_id in self._order if not self._deps[job_id]]

    def leaves(self):
        """Jobs nothing else waits for."""
        return [job_id for job_id in self._order if not self._dependents[job_id]]

    def edges(self):
        """Every (upstream, downstream) pair, in declaration order."""
        pairs = []
        for job_id in self._order:
            for dep in self._deps[job_id]:
                pairs.append((dep, job_id))
        return pairs

    # -- integrity -------------------------------------------------------

    def detect_cycle(self):
        """Return one cycle as a list of ids, or None when the graph is a DAG."""
        WHITE, GREY, BLACK = 0, 1, 2
        colour = {job_id: WHITE for job_id in self._order}
        stack = []

        def visit(node):
            colour[node] = GREY
            stack.append(node)
            for dep in ordered_unique(self._deps[node]):
                if colour[dep] == GREY:
                    start = stack.index(dep)
                    return stack[start:] + [dep]
                if colour[dep] == WHITE:
                    found = visit(dep)
                    if found:
                        return found
            colour[node] = BLACK
            stack.pop()
            return None

        for job_id in self._order:
            if colour[job_id] == WHITE:
                cycle = visit(job_id)
                if cycle:
                    return cycle
        return None

    def validate(self):
        """Raise GraphError unless the graph is a usable DAG."""
        cycle = self.detect_cycle()
        if cycle:
            raise GraphError("dependency cycle: " + " -> ".join(cycle))
        return self

    # -- derived graphs --------------------------------------------------

    def subgraph(self, job_ids):
        """A graph containing only `job_ids` and the edges between them."""
        wanted = [job_id for job_id in self._order if job_id in set(job_ids)]
        clone = DependencyGraph()
        for job_id in wanted:
            clone.add_job(self._jobs[job_id])
        for job_id in wanted:
            for dep in self._deps[job_id]:
                if dep in clone:
                    clone.add_dependency(job_id, dep)
        return clone

    def ancestors_of(self, job_id):
        """Every job that must run before `job_id`, transitively."""
        self._require(job_id)
        seen = []
        pending = list(self._deps[job_id])
        while pending:
            current = pending.pop(0)
            if current in seen:
                continue
            seen.append(current)
            pending.extend(self._deps[current])
        return [other for other in self._order if other in set(seen)]

    def descendants_of(self, job_id):
        """Every job that waits on `job_id`, transitively."""
        self._require(job_id)
        seen = set()
        pending = list(self._dependents[job_id])
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(self._dependents[current])
        return [other for other in self._order if other in seen]

    def to_rows(self):
        """Rows for the table renderer: id, action, dependency count."""
        return [
            (job_id, self._jobs[job_id].action, len(self._deps[job_id]))
            for job_id in self._order
        ]
