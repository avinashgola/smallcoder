"""The unit of work."""

from queueing.errors import QueueError


class Task:
    """One queued job.

    `max_attempts` is the total number of times the task may be executed,
    counting the first try. `None` means "use the worker's policy default".
    """

    __slots__ = ("id", "kind", "payload", "max_attempts", "priority", "tags")

    def __init__(self, id, kind, payload=None, max_attempts=None, priority=0, tags=()):
        if not isinstance(id, str) or not id.strip():
            raise QueueError("task id must be a non-empty string")
        if not isinstance(kind, str) or not kind.strip():
            raise QueueError("task kind must be a non-empty string")
        if max_attempts is not None and max_attempts < 1:
            raise QueueError("max_attempts must be at least 1")
        self.id = id.strip()
        self.kind = kind.strip()
        self.payload = dict(payload or {})
        self.max_attempts = max_attempts
        self.priority = int(priority)
        self.tags = tuple(tags)

    def has_tag(self, tag):
        return tag in self.tags

    def replace(self, **changes):
        """Return a copy with some fields changed."""
        fields = {
            "id": self.id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "max_attempts": self.max_attempts,
            "priority": self.priority,
            "tags": self.tags,
        }
        fields.update(changes)
        return Task(**fields)

    def describe(self):
        parts = ["%s(%s)" % (self.id, self.kind)]
        if self.max_attempts is not None:
            parts.append("max %d attempts" % self.max_attempts)
        if self.priority:
            parts.append("priority %d" % self.priority)
        if self.tags:
            parts.append("tags " + ",".join(self.tags))
        return ", ".join(parts)

    def __repr__(self):
        return "Task(%r, %r)" % (self.id, self.kind)

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id and self.kind == other.kind

    def __hash__(self):
        return hash((self.id, self.kind))
