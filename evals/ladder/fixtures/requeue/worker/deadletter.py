"""Where tasks go once the worker has given up on them."""

from queueing.errors import UnknownTask


class DeadLetter:
    """A task the worker abandoned, with the history that led there."""

    __slots__ = ("task", "outcome")

    def __init__(self, task, outcome):
        self.task = task
        self.outcome = outcome

    @property
    def attempts(self):
        return self.outcome.attempt_count

    @property
    def error(self):
        return self.outcome.error

    def __repr__(self):
        return "DeadLetter(%r, %d attempts)" % (self.task.id, self.attempts)


class DeadLetterQueue:
    """Keeps abandoned tasks so an operator can inspect or replay them."""

    def __init__(self):
        self._letters = []

    def add(self, task, outcome):
        letter = DeadLetter(task, outcome)
        self._letters.append(letter)
        return letter

    def ids(self):
        return [letter.task.id for letter in self._letters]

    def get(self, task_id):
        for letter in self._letters:
            if letter.task.id == task_id:
                return letter
        raise UnknownTask(task_id)

    def drain(self):
        """Take everything out of the dead letter queue."""
        letters = list(self._letters)
        self._letters = []
        return letters

    def replay_into(self, queue, task_ids=None):
        """Push abandoned tasks back onto `queue` and forget them."""
        wanted = set(task_ids) if task_ids is not None else None
        replayed = []
        keep = []
        for letter in self._letters:
            if wanted is None or letter.task.id in wanted:
                queue.push(letter.task)
                replayed.append(letter.task.id)
            else:
                keep.append(letter)
        self._letters = keep
        return replayed

    def summary(self):
        return {letter.task.id: letter.attempts for letter in self._letters}

    def __len__(self):
        return len(self._letters)
