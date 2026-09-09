from datetime import date

from recur.patterns import (
    DailyPattern,
    MonthlyByDayPattern,
    MonthlyByWeekdayPattern,
    WeeklyPattern,
)
from recur.spans import add_months, days_in_month, weeks_between
from recur.weekdays import WeekdayError, parse_weekdays


def test_weekday_parsing():
    assert parse_weekdays("mo,we,fr") == (0, 2, 4)
    assert parse_weekdays(["Tuesday", "th"]) == (1, 3)
    try:
        parse_weekdays("xx")
    except WeekdayError:
        pass
    else:
        raise AssertionError("unknown weekday should raise")


def test_span_helpers():
    assert days_in_month(2024, 2) == 29
    assert days_in_month(2023, 2) == 28
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert weeks_between(date(2024, 3, 4), date(2024, 3, 20)) == 2


def test_daily_pattern_honours_the_interval():
    pattern = DailyPattern(3)
    start = date(2024, 3, 4)
    assert pattern.matches(start, date(2024, 3, 7)) is True
    assert pattern.matches(start, date(2024, 3, 8)) is False
    assert pattern.matches(start, date(2024, 3, 1)) is False


def test_weekly_pattern_skips_off_weeks():
    pattern = WeeklyPattern("mo,we", interval=2)
    start = date(2024, 3, 4)
    assert pattern.matches(start, date(2024, 3, 6)) is True
    assert pattern.matches(start, date(2024, 3, 13)) is False
    assert pattern.matches(start, date(2024, 3, 20)) is True


def test_monthly_patterns():
    on_day = MonthlyByDayPattern(31)
    assert on_day.matches(date(2024, 1, 31), date(2024, 2, 29)) is True
    assert on_day.matches(date(2024, 1, 31), date(2024, 3, 30)) is False
    nth = MonthlyByWeekdayPattern("tu", 2)
    assert nth.matches(date(2024, 3, 1), date(2024, 4, 9)) is True
    assert nth.matches(date(2024, 3, 1), date(2024, 4, 2)) is False
    assert nth.describe() == "the 2nd Tuesday of the month"
