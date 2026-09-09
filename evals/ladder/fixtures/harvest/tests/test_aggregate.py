import pytest

from execution.outcome import State, StageOutcome
from harvester.aggregate import (
    dropped_per_stage,
    failure_reasons,
    slowest,
    state_tally,
    throughput,
    time_share,
    totals,
)
from harvester.filters import (
    after,
    dropping_at_least,
    failures,
    named,
    skipped,
    slower_than,
    split_failures,
    successes,
    with_state,
)

OUTCOMES = [
    StageOutcome("load", State.DONE, rows_in=10, rows_out=10, duration=0.5),
    StageOutcome("clean", State.DONE, rows_in=10, rows_out=7, duration=1.5),
    StageOutcome("score", State.FAILED, rows_in=7, rows_out=0, duration=0.25,
                 error="scorer offline"),
    StageOutcome("export", State.DONE, rows_in=7, rows_out=7, duration=0.75),
]


def test_totals_describe_the_whole_run():
    assert totals(OUTCOMES) == {
        "stages": 4,
        "rows_in": 10,
        "rows_out": 7,
        "dropped": 3,
        "duration": 3.0,
    }


def test_totals_of_nothing():
    assert totals([])["rows_in"] == 0
    assert totals([])["duration"] == 0.0


def test_state_tally_counts_each_state():
    assert state_tally(OUTCOMES).items() == [("done", 3), ("failed", 1)]


def test_dropped_per_stage_lists_only_lossy_stages():
    assert dropped_per_stage(OUTCOMES) == [("clean", 3), ("score", 7)]


def test_slowest_stages_come_first():
    assert [outcome.stage for outcome in slowest(OUTCOMES, count=2)] == [
        "clean",
        "export",
    ]


def test_time_share_adds_up():
    assert time_share(OUTCOMES) == [
        ("load", 16.7),
        ("clean", 50.0),
        ("score", 8.3),
        ("export", 25.0),
    ]


def test_throughput_uses_the_whole_run():
    assert throughput(OUTCOMES) == 2.3


def test_failure_reasons_are_keyed_by_stage():
    assert failure_reasons(OUTCOMES) == {"score": "scorer offline"}


MIXED = [
    StageOutcome("load", State.DONE, rows_in=10, rows_out=10, duration=0.5),
    StageOutcome("clean", State.DONE, rows_in=10, rows_out=7, duration=1.5),
    StageOutcome("score", State.FAILED, rows_in=7, duration=0.25, error="offline"),
    StageOutcome("export", State.SKIPPED, rows_in=7),
]


def names(outcomes):
    return [outcome.stage for outcome in outcomes]


def test_filter_by_state():
    assert names(with_state(MIXED, State.DONE)) == ["load", "clean"]
    assert names(failures(MIXED)) == ["score"]
    assert names(successes(MIXED)) == ["load", "clean"]
    assert names(skipped(MIXED)) == ["export"]
    with pytest.raises(ValueError):
        with_state(MIXED, "melted")


def test_filter_by_name():
    assert names(named(MIXED, {"clean", "export"})) == ["clean", "export"]
    assert named(MIXED, set()) == []


def test_filter_by_duration_and_drop():
    assert names(slower_than(MIXED, 0.5)) == ["clean"]
    assert names(dropping_at_least(MIXED, 3)) == ["clean", "score", "export"]
    assert names(dropping_at_least(MIXED, 8)) == []


def test_split_failures_keeps_order():
    failed, rest = split_failures(MIXED)
    assert names(failed) == ["score"]
    assert names(rest) == ["load", "clean", "export"]


def test_after_a_named_stage():
    assert names(after(MIXED, "clean")) == ["score", "export"]
    assert after(MIXED, "export") == []
    with pytest.raises(KeyError):
        after(MIXED, "nope")
