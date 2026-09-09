from queueing.backoff import Backoff
from queueing.errors import PermanentError, TransientError
from queueing.outcome import Outcome
from queueing.policy import RetryPolicy
from queueing.task import Task
from store.queue import TaskQueue
from support.clock import ManualClock, RecordingSleeper
from worker.dispatch import Dispatcher
from worker.loop import Worker

POLICY = RetryPolicy(max_attempts=3, backoff=Backoff(base=1.0, factor=2.0, cap=60.0))


def make_worker(handler, policy=POLICY, kind="email"):
    clock = ManualClock()
    sleeper = RecordingSleeper(clock)
    dispatcher = Dispatcher()
    dispatcher.register(kind, handler)
    worker = Worker(
        dispatcher=dispatcher, policy=policy, clock=clock, sleeper=sleeper
    )
    return worker, sleeper


def always_fails(calls, error=None):
    def handler(task, attempt):
        calls.append(attempt)
        raise error or TransientError("service unavailable")

    return handler


def test_a_task_that_works_runs_once():
    calls = []
    worker, sleeper = make_worker(lambda task, attempt: calls.append(attempt) or "ok")
    outcome = worker.run_task(Task("a", "email"))
    assert outcome.ok
    assert outcome.attempt_count == 1
    assert calls == [1]
    assert sleeper.delays == []


def test_a_task_that_recovers_stops_retrying():
    calls = []

    def handler(task, attempt):
        calls.append(attempt)
        if attempt < 2:
            raise TransientError("still warming up")
        return "ok"

    worker, sleeper = make_worker(handler)
    outcome = worker.run_task(Task("a", "email"))
    assert outcome.ok
    assert outcome.value == "ok"
    assert calls == [1, 2]
    assert sleeper.delays == [1.0]
    assert outcome.retries == 1


def test_the_attempt_budget_is_respected():
    calls = []
    worker, sleeper = make_worker(always_fails(calls))
    outcome = worker.run_task(Task("a", "email"))
    assert calls == [1, 2, 3]
    assert outcome.status == Outcome.FAILED
    assert outcome.attempt_count == 3
    assert sleeper.delays == [1.0, 2.0]


def test_a_task_may_shrink_its_own_budget():
    calls = []
    worker, sleeper = make_worker(always_fails(calls))
    outcome = worker.run_task(Task("a", "email", max_attempts=1))
    assert calls == [1]
    assert outcome.attempt_count == 1
    assert sleeper.delays == []


def test_a_task_may_raise_its_own_budget():
    calls = []
    worker, sleeper = make_worker(always_fails(calls))
    worker.run_task(Task("a", "email", max_attempts=4))
    assert calls == [1, 2, 3, 4]
    assert sleeper.delays == [1.0, 2.0, 4.0]


def test_permanent_failures_are_not_retried():
    calls = []
    worker, sleeper = make_worker(always_fails(calls, PermanentError("bad payload")))
    outcome = worker.run_task(Task("a", "email"))
    assert calls == [1]
    assert not outcome.ok
    assert sleeper.delays == []


def test_abandoned_tasks_land_in_the_dead_letter_queue():
    worker, _ = make_worker(always_fails([]))
    worker.run_task(Task("a", "email"))
    assert worker.dead_letters.ids() == ["a"]
    assert "TransientError" in worker.dead_letters.get("a").error


def test_attempts_are_logged():
    calls = []
    worker, _ = make_worker(always_fails(calls))
    worker.run_task(Task("a", "email"))
    logged = worker.log.for_task("a")
    assert [attempt.number for attempt in logged] == [1, 2, 3]
    assert all(not attempt.ok for attempt in logged)


def test_draining_a_queue_runs_every_due_task():
    seen = []
    worker, _ = make_worker(lambda task, attempt: seen.append(task.id))
    queue = TaskQueue(clock=ManualClock())
    queue.push_many([Task("a", "email"), Task("b", "email")])
    outcomes = worker.drain(queue)
    assert seen == ["a", "b"]
    assert worker.summary(outcomes) == {
        "tasks": 2,
        "succeeded": 2,
        "failed": 0,
        "attempts": 2,
        "retries": 0,
    }


def test_listener_sees_the_retry_events():
    events = []
    clock = ManualClock()
    dispatcher = Dispatcher()
    dispatcher.register("email", always_fails([]))
    worker = Worker(
        dispatcher=dispatcher,
        policy=POLICY,
        clock=clock,
        sleeper=RecordingSleeper(clock),
        listener=lambda event, payload: events.append(event),
    )
    worker.run_task(Task("a", "email"))
    assert events.count("retry") == 2
    assert events.count("gave_up") == 1


def test_error_supplied_delay_is_used():
    def handler(task, attempt):
        raise TransientError("slow down", retry_after=0.25)

    worker, sleeper = make_worker(handler)
    worker.run_task(Task("a", "email"))
    assert sleeper.delays[0] == 0.25
