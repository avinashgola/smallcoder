import pytest

from execution.errors import StageFailure
from execution.rows import drop_missing
from execution.session import Session
from execution.stagerun import Stage, stage
from harvester.aggregate import merge
from harvester.collector import ResultCollector
from harvester.history import History
from toolkit.timing import TickClock

ROWS = [{"id": 1, "amount": "10"}, {"id": 2}, {"id": 3, "amount": "7"}]


@stage("load")
def load(rows):
    return list(rows)


@stage("clean")
def clean(rows):
    return drop_missing(rows, ["amount"])


def broken(rows):
    raise StageFailure("upstream schema changed")


def summary(run_id, stages):
    session = Session("demo", stages, clock=TickClock(step=0.5))
    return ResultCollector("demo", run_id=run_id).collect(session.run(ROWS))


def clean_run(run_id):
    return summary(run_id, [load, clean])


def failed_run(run_id):
    return summary(run_id, [load, Stage("clean", broken)])


def test_history_keeps_the_runs_it_is_given():
    history = History("demo")
    history.add(clean_run("demo-001"))
    history.add(clean_run("demo-002"))
    assert history.run_ids() == ["demo-001", "demo-002"]
    assert len(history) == 2
    assert history.latest().run_id == "demo-002"


def test_empty_history():
    history = History("demo")
    assert history.latest() is None
    assert history.average_duration() == 0.0
    assert history.clean_run_share() == 0.0


def test_history_rejects_another_plan():
    history = History("demo")
    other = ResultCollector("other").collect(
        Session("other", [load], clock=TickClock(step=0.5)).run(ROWS)
    )
    with pytest.raises(ValueError):
        history.add(other)


def test_clean_run_share_and_durations():
    history = History("demo")
    history.add(clean_run("demo-001"))
    history.add(failed_run("demo-002"))
    assert history.clean_run_share() == 50.0
    assert history.average_duration() == 1.0
    assert history.failing_stages() == [("clean", 1)]


def test_slowest_runs():
    history = History("demo")
    first = clean_run("demo-001")
    second = clean_run("demo-002")
    second.duration = 5.0
    history.add(first)
    history.add(second)
    assert [s.run_id for s in history.slowest_runs(count=1)] == ["demo-002"]


def test_headline_merges_every_run():
    history = History("demo")
    history.add(clean_run("demo-001"))
    history.add(failed_run("demo-002"))
    headline = history.headline()
    assert headline["runs"] == 2
    assert headline["stages"] == 4
    assert headline["failed_stages"] == 1
    assert headline["clean_runs"] == 1
    assert merge([]) == {
        "runs": 0,
        "stages": 0,
        "failed_stages": 0,
        "rows_out": 0,
        "duration": 0.0,
        "clean_runs": 0,
    }
