"""Retry policy: how many attempts a task gets and how long to wait between.

Every method here counts *attempts already made*. The worker calls
`should_retry` right after an attempt failed, passing the number of attempts
that have been executed so far, so the first call of a task's life passes 1.
"""

from queueing.backoff import Backoff
from queueing.classify import DEFAULT_CLASSIFIER
from support.fmt import seconds


class RetryPolicy:
    """How stubborn the worker should be about one kind of failure."""

    def __init__(self, max_attempts=3, backoff=None, classifier=None):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.max_attempts = int(max_attempts)
        self.backoff = backoff or Backoff()
        self.classifier = classifier or DEFAULT_CLASSIFIER

    # -- decisions -------------------------------------------------------

    def should_retry(self, attempts_made, error):
        """True when a task that has failed `attempts_made` times gets another go."""
        if attempts_made < 1:
            raise ValueError("attempts_made starts at 1")
        if not self.classifier.is_retryable(error):
            return False
        return attempts_made <= self.max_attempts

    def delay_for(self, attempts_made, error=None):
        """How long to wait before the next attempt of a failing task."""
        requested = self.classifier.retry_after(error) if error is not None else None
        if requested is not None:
            return round(min(requested, self.backoff.cap), 6)
        return self.backoff.delay_for(attempts_made)

    def attempts_left(self, attempts_made):
        """How many further attempts the budget still allows."""
        return max(0, self.max_attempts - attempts_made)

    # -- derived policies ------------------------------------------------

    def for_task(self, task):
        """The policy that applies to one task, honouring its own override."""
        if task.max_attempts is None or task.max_attempts == self.max_attempts:
            return self
        return RetryPolicy(
            max_attempts=task.max_attempts,
            backoff=self.backoff,
            classifier=self.classifier,
        )

    def with_backoff(self, backoff):
        return RetryPolicy(
            max_attempts=self.max_attempts,
            backoff=backoff,
            classifier=self.classifier,
        )

    def with_classifier(self, classifier):
        return RetryPolicy(
            max_attempts=self.max_attempts,
            backoff=self.backoff,
            classifier=classifier,
        )

    @classmethod
    def from_config(cls, config):
        """Build a policy from a plain dictionary of settings."""
        config = dict(config or {})
        backoff = Backoff(
            base=config.get("base_delay", 0.5),
            factor=config.get("factor", 2.0),
            cap=config.get("cap", 30.0),
            jitter=config.get("jitter", 0.0),
            rand=config.get("rand"),
        )
        return cls(max_attempts=config.get("max_attempts", 3), backoff=backoff)

    # -- reporting -------------------------------------------------------

    def schedule(self):
        """The delays this policy would use, one per retry it allows."""
        return [self.delay_for(number) for number in range(1, self.max_attempts)]

    def describe(self):
        waits = ", ".join(seconds(delay) for delay in self.schedule()) or "no retries"
        return "up to %d attempts (%s); %s" % (
            self.max_attempts,
            self.backoff.describe(),
            waits,
        )


NO_RETRY = RetryPolicy(max_attempts=1)
