import pytest

from execution.errors import StageFailure
from execution.outcome import State, StageOutcome
from execution.rows import add_field, drop_missing
from execution.session import Session
from execution.stagerun import Stage, stage
from harvester.collector import ResultCollector
from harvester.errors import CollectError, NotSealed
from harvester.summary import RunSummary
from toolkit.timing import TickClock

ROWS = [
    {"id": 1, "region": "north", "amount": "10"},
    {"id": 2, "region": "south", "amount": "5"},
    {"id": 3, "region": "north"},
    {"id": 4, "region": "east", "amount": "7"},
]


@stage("load")
def load(rows):
    return list(rows)


@stage("clean")
def clean(rows):
    return drop_missing(rows, ["amount"])


@stage("score")
def score(rows):
    return add_field(rows, "score", lambda row: float(row.get("amount", 0)) * 2)


@stage("export")
def export(rows):
    return list(rows)


def broken(rows):
    raise StageFailure("upstream schema changed")


def run_clean_plan():
    session = Session("demo", [load, clean, score, export], clock=TickClock(step=0.5))
    return session.run(ROWS)


def run_with_failure(on_error="continue"):
    session = Session(
        "demo",
        [load, Stage("clean", broken), score, export],
        clock=TickClock(step=0.5),
        on_error=on_error,
    )
    return session.run(ROWS)


def collector():
    return ResultCollector("demo", run_id="demo-001")


def test_a_clean_run_is_collected_whole():
    summary = collector().collect(run_clean_plan())
    assert summary.stage_names() == ["load", "clean", "score", "export"]
    assert summary.succeeded_names() == ["load", "clean", "score", "export"]
    assert summary.ok


def test_a_clean_run_totals_the_whole_pass():
    summary = collector().collect(run_clean_plan())
    assert summary.rows_in == 4
    assert summary.rows_out == 3
    assert summary.duration == 2.0
    assert summary.sealed


def test_stages_after_a_failure_are_still_collected():
    summary = collector().collect(run_with_failure())
    assert summary.stage_names() == ["load", "clean", "score", "export"]
    assert summary.failed_names() == ["clean"]
    assert summary.succeeded_names() == ["load", "score", "export"]
    assert summary.stage_count == 4


def test_totals_of_a_failed_run_cover_the_whole_pass():
    summary = collector().collect(run_with_failure())
    assert summary.rows_in == 4
    assert summary.rows_out == 4
    assert summary.duration == 2.0
    assert summary.sealed
    assert not summary.ok


def test_skipped_stages_are_recorded_too():
    summary = collector().collect(run_with_failure(on_error="stop"))
    assert summary.skipped_names() == ["score", "export"]
    assert summary.failed_names() == ["clean"]
    assert summary.succeeded_names() == ["load"]
    assert summary.stage_count == 4


def test_summary_line_counts_every_stage():
    summary = collector().collect(run_with_failure())
    assert summary.summary_line() == (
        "demo/demo-001: 4 stage(s), 3 ok, 1 failed, 0 skipped, 4 rows in 2.0s"
    )


def test_outcome_lookup():
    summary = collector().collect(run_with_failure())
    assert summary.outcome_for("export").state == State.DONE
    with pytest.raises(KeyError):
        summary.outcome_for("nope")


def test_drop_warnings_are_collected():
    harvester = ResultCollector("demo", run_id="demo-001", warn_on_drop=1)
    harvester.collect(run_clean_plan())
    assert harvester.warnings == ["clean dropped 1 of 4 rows"]


def test_empty_and_duplicated_runs_are_rejected():
    with pytest.raises(CollectError):
        collector().collect([])
    twice = [
        StageOutcome("load", State.DONE),
        StageOutcome("load", State.DONE),
    ]
    with pytest.raises(CollectError):
        collector().collect(twice)


def test_collect_many_numbers_the_runs():
    summaries = ResultCollector("demo").collect_many(
        [run_clean_plan(), run_clean_plan()]
    )
    assert [summary.run_id for summary in summaries] == ["demo-001", "demo-002"]
    assert all(summary.sealed for summary in summaries)


def test_state_tally():
    tally = collector().state_tally(run_with_failure())
    assert tally.as_dict() == {"done": 3, "failed": 1}


def test_an_unsealed_summary_refuses_to_be_read():
    with pytest.raises(NotSealed):
        RunSummary("demo-001", "demo").require_sealed()
