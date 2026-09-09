"""A log of every attempt the worker has made, kept per task."""

from support.seq import counts_by


class AttemptLog:
    """Append-only record of attempts, grouped by task id."""

    def __init__(self):
        self._by_task = {}
        self._order = []

    def record(self, task_id, attempt):
        if task_id not in self._by_task:
            self._by_task[task_id] = []
            self._order.append(task_id)
        self._by_task[task_id].append(attempt)
        return attempt

    def record_all(self, task_id, attempts):
        for attempt in attempts:
            self.record(task_id, attempt)
        return self.for_task(task_id)

    def for_task(self, task_id):
        return list(self._by_task.get(task_id, ()))

    def attempt_count(self, task_id):
        return len(self._by_task.get(task_id, ()))

    def task_ids(self):
        return list(self._order)

    def total_attempts(self):
        return sum(len(items) for items in self._by_task.values())

    def failures(self):
        """Task ids whose last recorded attempt failed."""
        return [
            task_id
            for task_id in self._order
            if self._by_task[task_id] and not self._by_task[task_id][-1].ok
        ]

    def error_histogram(self):
        """How many attempts failed with each error text."""
        failed = [
            attempt
            for task_id in self._order
            for attempt in self._by_task[task_id]
            if not attempt.ok
        ]
        return counts_by(failed, lambda attempt: str(attempt.error))
