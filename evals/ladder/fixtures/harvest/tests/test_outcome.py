import pytest

from execution.outcome import State, StageOutcome
from execution.rows import (
    add_field,
    distinct_by,
    drop_missing,
    keep,
    project,
    rename,
    sum_field,
)

ROWS = [
    {"id": 1, "region": "north", "amount": "10"},
    {"id": 2, "region": "south", "amount": "5"},
    {"id": 3, "region": "north"},
]


def test_outcome_predicates():
    done = StageOutcome("load", State.DONE, rows_in=4, rows_out=3, duration=0.5)
    assert done.ok and not done.failed and not done.skipped
    assert done.dropped == 1
    assert done.rows_per_second == 6.0


def test_unknown_state_is_rejected():
    with pytest.raises(ValueError):
        StageOutcome("load", "exploded")


def test_outcome_rendering():
    failed = StageOutcome("clean", State.FAILED, rows_in=4, error="schema changed")
    assert failed.as_row() == ("clean", "failed", 4, 0, "0ms")
    assert "schema changed" in failed.describe()
    assert failed.to_dict()["error"] == "schema changed"
    assert failed.to_dict()["warnings"] == []
    assert repr(failed) == "StageOutcome('clean', failed)"


def test_row_filters():
    assert keep(ROWS, lambda row: row["region"] == "north") == [ROWS[0], ROWS[2]]
    assert drop_missing(ROWS, ["amount"]) == [ROWS[0], ROWS[1]]
    assert project(ROWS, ["id"]) == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_row_derivations():
    grown = add_field(ROWS[:1], "tag", lambda row: row["region"].upper())
    assert grown == [{"id": 1, "region": "north", "amount": "10", "tag": "NORTH"}]
    assert ROWS[0] == {"id": 1, "region": "north", "amount": "10"}
    assert rename(ROWS[:1], {"amount": "value"})[0]["value"] == "10"


def test_row_aggregates():
    assert sum_field(ROWS, "amount") == 15.0
    assert distinct_by(ROWS, "region") == [ROWS[0], ROWS[1]]
