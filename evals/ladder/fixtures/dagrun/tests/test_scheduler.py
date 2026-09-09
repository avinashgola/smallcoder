import pytest

from flow.errors import ScheduleError
from flow.graph import DependencyGraph
from flow.jobs import Job, Status
from flow.scheduler import Scheduler


def build(edges, ids=("a", "b", "c", "d")):
    graph = DependencyGraph()
    for job_id in ids:
        graph.add_job(Job(job_id, "noop"))
    for downstream, upstream in edges:
        graph.add_dependency(downstream, upstream)
    return graph


def test_roots_are_ready_first():
    scheduler = Scheduler(build([("b", "a"), ("c", "b"), ("d", "b")]))
    assert scheduler.ready() == ["a"]


def test_completing_a_job_unblocks_its_dependents():
    scheduler = Scheduler(build([("b", "a"), ("c", "a")]))
    scheduler.take()
    assert scheduler.mark_succeeded("a") == ["b", "c"]
    assert scheduler.ready() == ["b", "c"]


def test_a_job_waits_for_every_dependency():
    scheduler = Scheduler(build([("c", "a"), ("c", "b")]))
    scheduler.take()
    assert scheduler.mark_succeeded("a") == []
    assert scheduler.mark_succeeded("b") == ["c"]


def test_repeated_dependency_counts_once():
    graph = build([("b", "a"), ("b", "a")], ids=("a", "b"))
    scheduler = Scheduler(graph)
    assert scheduler.waiting_on("b") == 1
    scheduler.take()
    assert scheduler.mark_succeeded("a") == ["b"]


def test_failure_skips_everything_downstream():
    scheduler = Scheduler(build([("b", "a"), ("c", "b"), ("d", "a")]))
    scheduler.take()
    assert sorted(scheduler.mark_failed("a")) == ["b", "c", "d"]
    assert scheduler.is_done()


def test_waves_group_parallel_jobs():
    scheduler = Scheduler(build([("b", "a"), ("c", "a"), ("d", "b"), ("d", "c")]))
    assert scheduler.waves() == [["a"], ["b", "c"], ["d"]]


def test_linear_order_is_a_valid_topological_order():
    scheduler = Scheduler(build([("b", "a"), ("c", "b"), ("d", "c")]))
    assert scheduler.linear_order() == ["a", "b", "c", "d"]


def test_take_reports_a_stalled_run():
    scheduler = Scheduler(build([("b", "a")], ids=("a", "b")))
    scheduler.take()
    with pytest.raises(ScheduleError):
        scheduler.take()


def test_terminal_jobs_cannot_be_marked_twice():
    scheduler = Scheduler(build([], ids=("a",)))
    scheduler.take()
    scheduler.mark_succeeded("a")
    with pytest.raises(ScheduleError):
        scheduler.mark_failed("a")


def test_status_tracking():
    scheduler = Scheduler(build([("b", "a")], ids=("a", "b")))
    assert scheduler.status_of("a") == Status.PENDING
    scheduler.take()
    assert scheduler.status_of("a") == Status.RUNNING
    scheduler.mark_succeeded("a")
    assert scheduler.status_of("a") == Status.SUCCEEDED
    assert scheduler.remaining() == ["b"]
