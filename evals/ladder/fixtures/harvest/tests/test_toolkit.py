import pytest

from toolkit.timing import FrozenClock, TickClock
from toolkit.counters import Tally, sum_by
from toolkit.sorting import partition, sorted_by, top_n, unique
from toolkit.tables import render_table, truncate, widths_for
from toolkit.timing import format_duration, rate_per_second, share, total_seconds


def test_tally_keeps_insertion_order():
    tally = Tally(["b", "a", "b"])
    assert tally.names() == ["b", "a"]
    assert tally.get("b") == 2
    assert tally.get("missing") == 0
    assert tally.total() == 3
    assert len(tally) == 2
    assert "a" in tally


def test_tally_most_common_breaks_ties_by_name():
    tally = Tally(["b", "a", "b", "c"])
    assert tally.most_common(2) == [("b", 2), ("a", 1)]
    assert tally.as_dict() == {"a": 1, "b": 2, "c": 1}


def test_sum_by():
    rows = [("a", 2), ("b", 3), ("a", 4)]
    tally = sum_by(rows, key=lambda r: r[0], value=lambda r: r[1])
    assert tally.items() == [("a", 6), ("b", 3)]


def test_tick_clock_advances_on_every_read():
    clock = TickClock(start=1.0, step=0.5)
    assert clock() == 1.0
    assert clock() == 1.5
    assert clock.reads == 2
    with pytest.raises(ValueError):
        TickClock(step=-1)


def test_frozen_clock_only_moves_on_demand():
    clock = FrozenClock(start=2.0)
    assert clock() == 2.0
    clock.advance(1.0)
    assert clock() == 3.0


def test_duration_formatting():
    assert format_duration(0.0) == "0ms"
    assert format_duration(0.25) == "250ms"
    assert format_duration(1.5) == "1.5s"
    assert format_duration(125.0) == "2m05s"


def test_rates_and_shares():
    assert rate_per_second(10, 2.0) == 5.0
    assert rate_per_second(10, 0) == 0.0
    assert share(1, 4) == 25.0
    assert share(1, 0) == 0.0
    assert total_seconds([0.5, 0.25]) == 0.75


def test_sorting_helpers():
    items = [("a", 2), ("b", 2), ("c", 1)]
    assert sorted_by(items, key=lambda i: i[1]) == [("c", 1), ("a", 2), ("b", 2)]
    assert top_n(items, key=lambda i: i[1], count=2) == [("a", 2), ("b", 2)]
    assert top_n(items, key=lambda i: i[1], count=0) == []
    assert partition(items, lambda i: i[1] == 2) == ([("a", 2), ("b", 2)], [("c", 1)])
    assert unique([1, 2, 1, 3]) == [1, 2, 3]


def test_table_rendering():
    rows = [("load", 4), ("cleanup-the-columns", 2)]
    assert truncate("abcdefg", 5) == "ab..."
    assert widths_for(rows, ("stage", "n"), limit=8) == [8, 1]
    table = render_table(rows, ("stage", "n"), limit=8)
    lines = table.splitlines()
    assert lines[0].startswith("stage")
    assert lines[1].startswith("--------")
    assert lines[2].startswith("load")
