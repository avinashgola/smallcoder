import pytest

from support.clock import ManualClock, RecordingSleeper
from support.fmt import attempt_label, bullet_list, seconds, truncate
from support.rng import ConstantJitter, CycleJitter
from support.seq import chunked, counts_by, first, last, take_while


def test_manual_clock_only_moves_on_demand():
    clock = ManualClock(start=5.0)
    assert clock() == 5.0
    clock.advance(2.5)
    assert clock() == 7.5
    with pytest.raises(ValueError):
        clock.advance(-1)


def test_recording_sleeper_advances_its_clock():
    clock = ManualClock()
    sleeper = RecordingSleeper(clock)
    sleeper(0.5)
    sleeper(1.5)
    assert sleeper.delays == [0.5, 1.5]
    assert sleeper.total == 2.0
    assert clock() == 2.0


def test_jitter_sources():
    assert ConstantJitter(0.25)() == 0.25
    cycle = CycleJitter([0.1, 0.2])
    assert [cycle(), cycle(), cycle()] == [0.1, 0.2, 0.1]
    with pytest.raises(ValueError):
        ConstantJitter(1.0)


def test_formatting():
    assert seconds(0.25) == "250ms"
    assert seconds(2.0) == "2.0s"
    assert seconds(65.0) == "1m05s"
    assert attempt_label(2, 5) == "attempt 2/5"
    assert truncate("abcdefgh", 5) == "ab..."
    assert bullet_list(["a", "b"]) == "- a\n- b"


def test_sequence_helpers():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert first([], default="x") == "x"
    assert last([1, 2, 3]) == 3
    assert take_while([1, 2, 9, 3], lambda n: n < 5) == [1, 2]
    assert counts_by(["a", "b", "a"], lambda s: s) == {"a": 2, "b": 1}
