from spans.parse import DurationError, parse_clock, parse_compact, parse_duration, parse_iso
from spans.units import UnitError, normalise_unit, unit_seconds


def test_unit_spellings():
    assert normalise_unit("Hours") == "h"
    assert normalise_unit("min") == "m"
    assert unit_seconds("day") == 86400
    try:
        normalise_unit("fortnights")
    except UnitError:
        pass
    else:
        raise AssertionError("unknown unit should raise")


def test_compact_form():
    assert parse_compact("1h30m") == 5400
    assert parse_compact("2d 4h") == 187200
    assert parse_compact("90 min") == 5400
    assert parse_compact("1.5h") == 5400


def test_compact_form_rejects_junk():
    try:
        parse_compact("about an hour")
    except DurationError:
        pass
    else:
        raise AssertionError("free text should raise")


def test_clock_form():
    assert parse_clock("1:30") == 90
    assert parse_clock("01:30:00") == 5400
    assert parse_clock("100:00:00") == 360000


def test_iso_form():
    assert parse_iso("PT1H30M") == 5400
    assert parse_iso("P1DT2H") == 93600
    assert parse_iso("P2W") == 1209600
    assert parse_iso("-PT45S") == -45


def test_dispatch_covers_every_spelling():
    assert parse_duration("1h30m") == 5400
    assert parse_duration("01:30:00") == 5400
    assert parse_duration("PT1H30M") == 5400
    assert parse_duration("5400") == 5400
    assert parse_duration("-1h30m") == -5400
    assert parse_duration(5400) == 5400
