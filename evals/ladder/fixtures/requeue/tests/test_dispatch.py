import pytest

from queueing.errors import QueueError
from queueing.task import Task
from worker.deadletter import DeadLetterQueue
from worker.dispatch import Dispatcher
from worker.metrics import Metrics
from queueing.outcome import Outcome, TaskOutcome
from store.queue import TaskQueue
from support.clock import ManualClock


def test_register_and_resolve():
    dispatcher = Dispatcher()
    dispatcher.register("email", lambda task, attempt: "sent")
    assert dispatcher.resolve(Task("a", "email"))(None, 1) == "sent"
    assert dispatcher.kinds() == ["email"]


def test_decorator_form():
    dispatcher = Dispatcher()

    @dispatcher.register("sms")
    def send(task, attempt):
        return "sms"

    assert dispatcher.handles("sms")
    assert dispatcher.resolve(Task("a", "sms")) is send


def test_fallback_handler():
    dispatcher = Dispatcher()
    dispatcher.fallback(lambda task, attempt: "generic")
    assert dispatcher.resolve(Task("a", "unknown"))(None, 1) == "generic"


def test_missing_handler_is_reported():
    dispatcher = Dispatcher()
    with pytest.raises(QueueError):
        dispatcher.resolve(Task("a", "email"))
    assert dispatcher.unhandled([Task("a", "email"), Task("b", "sms")]) == [
        "email",
        "sms",
    ]


def test_metrics_counters_and_timers():
    metrics = Metrics()
    metrics.incr("attempts")
    metrics.incr("attempts", 2)
    metrics.observe("runtime", 0.5)
    metrics.observe("runtime", 1.5)
    assert metrics.get("attempts") == 3
    assert metrics.total("runtime") == 2.0
    assert metrics.mean("runtime") == 1.0
    assert metrics.snapshot()["runtime_total"] == 2.0
    assert "attempts=3" in metrics.describe()


def test_dead_letters_can_be_replayed():
    task = Task("a", "email")
    letters = DeadLetterQueue()
    letters.add(task, TaskOutcome("a", Outcome.FAILED, [], error="boom"))
    assert letters.ids() == ["a"]
    assert letters.get("a").error == "boom"
    queue = TaskQueue(clock=ManualClock())
    assert letters.replay_into(queue) == ["a"]
    assert len(letters) == 0
    assert queue.pop().id == "a"


def test_dead_letters_drain():
    letters = DeadLetterQueue()
    letters.add(Task("a", "email"), TaskOutcome("a", Outcome.FAILED, []))
    assert len(letters.drain()) == 1
    assert len(letters) == 0
