import pytest

from queueing.errors import QueueError, UnknownTask
from queueing.task import Task
from store.queue import TaskQueue
from store.records import AttemptLog
from queueing.outcome import Attempt
from support.clock import ManualClock


def make_queue():
    clock = ManualClock()
    return TaskQueue(clock=clock), clock


def test_fifo_within_a_priority_level():
    queue, _ = make_queue()
    queue.push_many([Task("a", "email"), Task("b", "email")])
    assert queue.pop().id == "a"
    assert queue.pop().id == "b"
    assert queue.pop() is None


def test_higher_priority_jumps_the_line():
    queue, _ = make_queue()
    queue.push(Task("a", "email"))
    queue.push(Task("b", "email", priority=5))
    assert queue.pop().id == "b"


def test_delayed_tasks_stay_hidden_until_due():
    queue, clock = make_queue()
    queue.push(Task("later", "email"), delay=5.0)
    assert len(queue) == 1
    assert queue.due_count() == 0
    assert queue.pop() is None
    clock.advance(5.0)
    assert queue.due_count() == 1
    assert queue.pop().id == "later"


def test_ids_lists_due_tasks_first():
    queue, _ = make_queue()
    queue.push(Task("now", "email"))
    queue.push(Task("soon", "email"), delay=1.0)
    assert queue.ids() == ["now", "soon"]
    assert queue.hidden_count() == 1


def test_duplicate_ids_are_rejected():
    queue, _ = make_queue()
    queue.push(Task("a", "email"))
    with pytest.raises(QueueError):
        queue.push(Task("a", "email"))


def test_remove_unknown_task():
    queue, _ = make_queue()
    with pytest.raises(UnknownTask):
        queue.remove("ghost")


def test_membership_and_peek():
    queue, _ = make_queue()
    queue.push(Task("a", "email"))
    assert "a" in queue
    assert queue.peek().id == "a"
    assert len(queue) == 1


def test_attempt_log_groups_by_task():
    log = AttemptLog()
    log.record("a", Attempt(1, ok=False, error="boom"))
    log.record("a", Attempt(2, ok=True))
    log.record("b", Attempt(1, ok=False, error="boom"))
    assert log.task_ids() == ["a", "b"]
    assert log.attempt_count("a") == 2
    assert log.total_attempts() == 3
    assert log.failures() == ["b"]
    assert log.error_histogram() == {"boom": 2}
