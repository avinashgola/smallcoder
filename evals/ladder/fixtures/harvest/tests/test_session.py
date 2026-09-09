import pytest

from execution.errors import PlanError, StageFailure
from execution.outcome import State
from execution.rows import add_field, drop_missing
from execution.session import Session
from execution.stagerun import Stage, run_stage, stage
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


def broken(rows):
    raise StageFailure("upstream schema changed")


def test_stage_construction_is_validated():
    assert load.name == "load"
    assert load.describe() == "load"
    assert Stage("opt", lambda rows: rows, critical=False).describe() == "opt (optional)"
    with pytest.raises(PlanError):
        Stage("", lambda rows: rows)
    with pytest.raises(PlanError):
        Stage("x", "not callable")


def test_run_stage_reports_counts_and_duration():
    rows_out, outcome = run_stage(clean, ROWS, TickClock(step=0.5))
    assert len(rows_out) == 3
    assert outcome.state == State.DONE
    assert outcome.rows_in == 4
    assert outcome.rows_out == 3
    assert outcome.duration == 0.5


def test_a_failing_stage_passes_its_input_through():
    rows_out, outcome = run_stage(Stage("boom", broken), ROWS, TickClock(step=0.5))
    assert rows_out == ROWS
    assert outcome.state == State.FAILED
    assert outcome.error == "upstream schema changed"


def test_an_unexpected_error_is_still_a_failure():
    def explode(rows):
        raise ValueError("bad row")

    _, outcome = run_stage(Stage("boom", explode), ROWS, TickClock(step=0.5))
    assert outcome.state == State.FAILED
    assert outcome.error == "ValueError: bad row"


def test_session_runs_every_stage_in_order():
    session = Session("demo", [load, clean, score], clock=TickClock(step=0.5))
    outcomes = session.run(ROWS)
    assert [outcome.stage for outcome in outcomes] == ["load", "clean", "score"]
    assert [outcome.state for outcome in outcomes] == [State.DONE] * 3
    assert outcomes[-1].rows_out == 3
    assert session.describe() == "demo: load -> clean -> score"


def test_continue_mode_keeps_going_after_a_failure():
    session = Session(
        "demo", [load, Stage("clean", broken), score], clock=TickClock(step=0.5)
    )
    outcomes = session.run(ROWS)
    assert [outcome.state for outcome in outcomes] == [
        State.DONE,
        State.FAILED,
        State.DONE,
    ]
    assert outcomes[2].rows_in == 4


def test_stop_mode_skips_the_rest():
    session = Session(
        "demo",
        [load, Stage("clean", broken), score],
        clock=TickClock(step=0.5),
        on_error="stop",
    )
    outcomes = session.run(ROWS)
    assert [outcome.state for outcome in outcomes] == [
        State.DONE,
        State.FAILED,
        State.SKIPPED,
    ]
    assert outcomes[2].error == "earlier stage failed"


def test_an_optional_stage_does_not_stop_the_run():
    session = Session(
        "demo",
        [load, Stage("clean", broken, critical=False), score],
        clock=TickClock(step=0.5),
        on_error="stop",
    )
    assert [o.state for o in session.run(ROWS)] == [State.DONE, State.FAILED, State.DONE]


def test_plans_are_validated():
    with pytest.raises(PlanError):
        Session("demo", [])
    with pytest.raises(PlanError):
        Session("demo", [load, load])
    with pytest.raises(PlanError):
        Session("demo", [load], on_error="panic")


def test_run_ids_count_runs():
    session = Session("demo", [load], clock=TickClock(step=0.5))
    session.run(ROWS)
    assert session.run_id() == "demo-001"
    session.run(ROWS)
    assert session.run_id() == "demo-002"
    assert len(session) == 1
