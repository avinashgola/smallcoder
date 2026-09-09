from spans.arith import clamp, combine, round_nearest, round_up, scale, split
from spans.render import clock, compact, human, iso


def test_split_and_combine_round_trip():
    assert split(93784) == (1, 2, 3, 4)
    assert combine(1, 2, 3, 4) == 93784
    assert split(0) == (0, 0, 0, 0)


def test_rounding_helpers():
    assert round_up(5401, 900) == 6300
    assert round_up(5400, 900) == 5400
    assert round_nearest(5401, 900) == 5400
    assert round_nearest(5850, 900) == 6300


def test_clamp_and_scale():
    assert clamp(5400, low=7200) == 7200
    assert clamp(5400, high=1800) == 1800
    assert clamp(5400, low=0, high=86400) == 5400
    assert scale(5400, 1.5) == 8100
    assert scale(-5400, 1.5) == -8100


def test_compact_rendering():
    assert compact(5400) == "1h30m"
    assert compact(93784) == "1d2h3m4s"
    assert compact(0) == "0s"
    assert compact(-90) == "-1m30s"


def test_clock_rendering():
    assert clock(5400) == "01:30:00"
    assert clock(93784) == "26:03:04"


def test_human_rendering():
    assert human(5400) == "1 hour 30 minutes"
    assert human(93784) == "1 day 2 hours"
    assert human(93784, max_parts=4) == "1 day 2 hours 3 minutes 4 seconds"
    assert human(0) == "0 seconds"


def test_iso_rendering():
    assert iso(5400) == "PT1H30M"
    assert iso(93784) == "P1DT2H3M4S"
    assert iso(0) == "PT0S"
