"""A small in-memory task queue with priorities and delayed re-delivery."""

from queueing.errors import QueueError, UnknownTask
from support.clock import system_clock


class Entry:
    """A queued task plus the time it becomes visible again."""

    __slots__ = ("task", "due_at", "sequence")

    def __init__(self, task, due_at, sequence):
        self.task = task
        self.due_at = float(due_at)
        self.sequence = int(sequence)

    def is_due(self, now):
        return self.due_at <= now

    def __repr__(self):
        return "Entry(%r, due=%g)" % (self.task.id, self.due_at)


class TaskQueue:
    """FIFO within a priority level; higher priority tasks come out first."""

    def __init__(self, clock=None):
        self._clock = clock or system_clock
        self._entries = []
        self._sequence = 0

    def push(self, task, delay=0.0):
        """Add a task, optionally hidden for `delay` seconds."""
        if delay < 0:
            raise QueueError("delay cannot be negative")
        if any(entry.task.id == task.id for entry in self._entries):
            raise QueueError("task %r is already queued" % (task.id,))
        self._sequence += 1
        self._entries.append(Entry(task, self._clock() + delay, self._sequence))
        return task

    def push_many(self, tasks):
        return [self.push(task) for task in tasks]

    def pop(self):
        """Remove and return the next due task, or None when nothing is due."""
        entry = self.peek_entry()
        if entry is None:
            return None
        self._entries.remove(entry)
        return entry.task

    def peek_entry(self):
        now = self._clock()
        due = [entry for entry in self._entries if entry.is_due(now)]
        if not due:
            return None
        due.sort(key=lambda entry: (-entry.task.priority, entry.sequence))
        return due[0]

    def peek(self):
        entry = self.peek_entry()
        return None if entry is None else entry.task

    def remove(self, task_id):
        for entry in self._entries:
            if entry.task.id == task_id:
                self._entries.remove(entry)
                return entry.task
        raise UnknownTask(task_id)

    def due_count(self):
        now = self._clock()
        return sum(1 for entry in self._entries if entry.is_due(now))

    def hidden_count(self):
        return len(self._entries) - self.due_count()

    def ids(self):
        """Queued ids in delivery order, due first then by wake-up time."""
        now = self._clock()
        ordered = sorted(
            self._entries,
            key=lambda entry: (
                not entry.is_due(now),
                entry.due_at if not entry.is_due(now) else 0,
                -entry.task.priority,
                entry.sequence,
            ),
        )
        return [entry.task.id for entry in ordered]

    def __len__(self):
        return len(self._entries)

    def __contains__(self, task_id):
        return any(entry.task.id == task_id for entry in self._entries)
