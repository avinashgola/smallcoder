"""The job data model."""

from util.ids import normalize_id
from util.sets import ordered_unique


class Status:
    """Lifecycle states a job moves through during a run."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"

    TERMINAL = (SUCCEEDED, FAILED, SKIPPED)
    ALL = (PENDING, READY, RUNNING, SUCCEEDED, FAILED, SKIPPED)


class Job:
    """One unit of work plus the metadata the scheduler needs."""

    __slots__ = ("id", "action", "params", "after", "tags", "critical")

    def __init__(self, id, action, params=None, after=(), tags=(), critical=True):
        self.id = normalize_id(id)
        self.action = action
        self.params = dict(params or {})
        self.after = tuple(after)
        self.tags = tuple(ordered_unique(tags))
        self.critical = bool(critical)

    def with_params(self, **extra):
        """Return a copy with additional parameters merged in."""
        merged = dict(self.params)
        merged.update(extra)
        return Job(
            self.id,
            self.action,
            params=merged,
            after=self.after,
            tags=self.tags,
            critical=self.critical,
        )

    def has_tag(self, tag):
        return tag in self.tags

    def describe(self):
        parts = ["%s -> %s" % (self.id, self.action)]
        if self.after:
            parts.append("after " + ", ".join(self.after))
        if self.tags:
            parts.append("tags " + ",".join(self.tags))
        if not self.critical:
            parts.append("non-critical")
        return "; ".join(parts)

    def __repr__(self):
        return "Job(%r, %r)" % (self.id, self.action)

    def __eq__(self, other):
        if not isinstance(other, Job):
            return NotImplemented
        return (
            self.id == other.id
            and self.action == other.action
            and self.params == other.params
            and self.after == other.after
            and self.tags == other.tags
            and self.critical == other.critical
        )

    def __hash__(self):
        return hash((self.id, self.action))


def sort_jobs(jobs):
    """Stable ordering used whenever jobs are printed rather than executed."""
    return sorted(jobs, key=lambda job: job.id)
