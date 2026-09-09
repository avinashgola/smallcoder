"""The execution loop.

`Worker.run_task` executes one task and keeps trying while the retry policy
allows it. The loop counts *executions*: `attempts_made` is incremented before
each call, so once the handler has raised, `attempts_made` is exactly how many
times the task has run. That same number is what the policy is asked about and
what the backoff is asked for, which is why both of those take "attempts
already made" rather than "the attempt about to happen".

`Worker.drain` repeats that for every task in a queue.
"""

from queueing.errors import QueueError
from queueing.outcome import Attempt, Outcome, TaskOutcome
from queueing.policy import RetryPolicy
from store.records import AttemptLog
from support.clock import system_clock, system_sleeper
from worker.deadletter import DeadLetterQueue
from worker.dispatch import Dispatcher
from worker.metrics import Metrics


class Worker:
    """Runs tasks, retrying failures according to a policy."""

    def __init__(
        self,
        dispatcher=None,
        policy=None,
        clock=None,
        sleeper=None,
        log=None,
        dead_letters=None,
        metrics=None,
        listener=None,
    ):
        self.dispatcher = Dispatcher() if dispatcher is None else dispatcher
        self.policy = RetryPolicy() if policy is None else policy
        self.clock = system_clock if clock is None else clock
        self.sleeper = system_sleeper if sleeper is None else sleeper
        self.log = AttemptLog() if log is None else log
        self.dead_letters = DeadLetterQueue() if dead_letters is None else dead_letters
        self.metrics = Metrics() if metrics is None else metrics
        self.listener = listener

    # -- running one task ------------------------------------------------

    def run_task(self, task):
        """Execute `task`, retrying while the policy allows, and report."""
        handler = self.dispatcher.resolve(task)
        policy = self.policy.for_task(task)
        attempts = []
        attempts_made = 0
        pending_delay = 0.0

        while True:
            attempts_made += 1
            self._notify("attempt_start", task=task, attempt=attempts_made)
            started = self.clock()
            try:
                value = handler(task, attempts_made)
            except Exception as error:
                attempt = self._failed_attempt(
                    task, attempts_made, error, started, pending_delay
                )
                attempts.append(attempt)
                if not policy.should_retry(attempts_made, error):
                    return self._give_up(task, attempts, error)
                pending_delay = policy.delay_for(attempts_made, error)
                self.metrics.incr("retries")
                self.metrics.observe("delay", pending_delay)
                self._notify("retry", task=task, attempt=attempts_made,
                             delay=pending_delay)
                self.sleeper(pending_delay)
                continue

            attempt = self._succeeded_attempt(task, attempts_made, started,
                                              pending_delay)
            attempts.append(attempt)
            self.metrics.incr("succeeded")
            self._notify("success", task=task, attempt=attempts_made)
            return TaskOutcome(task.id, Outcome.SUCCEEDED, attempts, value=value)

    # -- running many ----------------------------------------------------

    def drain(self, queue, limit=None):
        """Run every due task in `queue`; returns the outcomes in run order."""
        outcomes = []
        while limit is None or len(outcomes) < limit:
            task = queue.pop()
            if task is None:
                break
            outcomes.append(self.run_task(task))
        return outcomes

    def run_all(self, tasks):
        return [self.run_task(task) for task in tasks]

    def summary(self, outcomes):
        """Aggregate a batch of outcomes into a small report dictionary."""
        return {
            "tasks": len(outcomes),
            "succeeded": sum(1 for outcome in outcomes if outcome.ok),
            "failed": sum(1 for outcome in outcomes if not outcome.ok),
            "attempts": sum(outcome.attempt_count for outcome in outcomes),
            "retries": sum(outcome.retries for outcome in outcomes),
        }

    # -- internals -------------------------------------------------------

    def _failed_attempt(self, task, number, error, started, delay_before):
        duration = round(self.clock() - started, 6)
        attempt = Attempt(
            number,
            ok=False,
            error="%s: %s" % (type(error).__name__, error),
            duration=duration,
            delay_before=delay_before,
        )
        self.log.record(task.id, attempt)
        self.metrics.incr("attempts")
        self.metrics.observe("runtime", duration)
        self._notify("attempt_failed", task=task, attempt=number, error=error)
        return attempt

    def _succeeded_attempt(self, task, number, started, delay_before):
        duration = round(self.clock() - started, 6)
        attempt = Attempt(
            number, ok=True, duration=duration, delay_before=delay_before
        )
        self.log.record(task.id, attempt)
        self.metrics.incr("attempts")
        self.metrics.observe("runtime", duration)
        return attempt

    def _give_up(self, task, attempts, error):
        detail = "%s: %s" % (type(error).__name__, error)
        outcome = TaskOutcome(task.id, Outcome.FAILED, attempts, error=detail)
        self.dead_letters.add(task, outcome)
        self.metrics.incr("failed")
        self._notify("gave_up", task=task, attempts=len(attempts), error=error)
        return outcome

    def _notify(self, event, **payload):
        if self.listener is not None:
            self.listener(event, payload)


def run_once(task, handler, policy=None, **kwargs):
    """Convenience wrapper: run a single task with an inline handler."""
    dispatcher = Dispatcher()
    dispatcher.register(task.kind, handler)
    if not isinstance(task.kind, str):
        raise QueueError("task kind must be a string")
    return Worker(dispatcher=dispatcher, policy=policy, **kwargs).run_task(task)
