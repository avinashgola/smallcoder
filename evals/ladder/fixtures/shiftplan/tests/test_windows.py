from shifts.clock import ClockError, format_span, format_time, parse_time
from shifts.templates import UnknownShift, describe, names, night_shifts, template
from shifts.window import Window


def test_clock_round_trip():
    assert parse_time("06:00") == 360
    assert parse_time("22:30") == 1350
    assert format_time(1320) == "22:00"
    assert format_time(1440) == "00:00"


def test_clock_rejects_nonsense():
    for text in ("25:00", "6", "06:99"):
        try:
            parse_time(text)
        except ClockError:
            continue
        raise AssertionError("expected %r to be rejected" % (text,))


def test_span_formatting():
    assert format_span(480) == "8h"
    assert format_span(450) == "7h30m"


def test_day_windows():
    window = Window.from_text("06:00-14:00")
    assert (window.start, window.duration) == (360, 480)
    assert window.end == 840
    assert window.crosses_midnight is False
    assert window.text() == "06:00-14:00"
    assert window.label() == "06:00-14:00 (8h)"


def test_windows_that_run_past_midnight():
    night = Window.from_text("22:00-06:00")
    assert night.duration == 480
    assert night.crosses_midnight is True
    assert night.end == 360
    ends_at_midnight = Window.from_text("16:00-00:00")
    assert ends_at_midnight.duration == 480
    assert ends_at_midnight.crosses_midnight is False


def test_malformed_windows_are_rejected():
    for text in ("06:00", "06:00-06:00"):
        try:
            Window.from_text(text)
        except ClockError:
            continue
        raise AssertionError("expected %r to be rejected" % (text,))


def test_named_shifts():
    assert names() == ["early", "half", "late", "night"]
    assert template("Early") == Window.from_text("06:00-14:00")
    assert describe("late") == "late 14:00-22:00 (8h)"
    assert night_shifts() == ["night"]
    try:
        template("brunch")
    except UnknownShift:
        pass
    else:
        raise AssertionError("unknown shift should raise")
