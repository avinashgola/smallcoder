from datetime import date

from recur.patterns import DailyPattern
from recur.rules import RecurrenceRule, daily, monthly_on_day, monthly_on_weekday, weekly


def test_count_caps_the_series():
    rule = daily(date(2024, 3, 4), count=3)
    assert list(rule.occurrences()) == [
        date(2024, 3, 4),
        date(2024, 3, 5),
        date(2024, 3, 6),
    ]


def test_until_is_inclusive():
    rule = daily(date(2024, 3, 4), until=date(2024, 3, 7))
    assert list(rule.occurrences())[-1] == date(2024, 3, 7)


def test_open_ended_rule_needs_a_bound():
    try:
        list(daily(date(2024, 3, 4)).occurrences())
    except ValueError:
        pass
    else:
        raise AssertionError("an unbounded rule should refuse to expand")


def test_between_is_half_open():
    rule = weekly(date(2024, 3, 4), "mo,we,fr")
    assert rule.between(date(2024, 3, 6), date(2024, 3, 13)) == [
        date(2024, 3, 6),
        date(2024, 3, 8),
        date(2024, 3, 11),
    ]


def test_explicit_exclusions_skip_without_consuming_the_count():
    rule = RecurrenceRule(
        DailyPattern(1), date(2024, 3, 4), count=3, exclusions=[date(2024, 3, 5)]
    )
    assert list(rule.occurrences()) == [
        date(2024, 3, 4),
        date(2024, 3, 6),
        date(2024, 3, 7),
    ]


def test_monthly_rules():
    on_day = monthly_on_day(date(2024, 1, 31), 31)
    assert on_day.between(date(2024, 1, 1), date(2024, 5, 1)) == [
        date(2024, 1, 31),
        date(2024, 2, 29),
        date(2024, 3, 31),
        date(2024, 4, 30),
    ]
    board = monthly_on_weekday(date(2024, 3, 1), "tu", 2)
    assert board.between(date(2024, 3, 1), date(2024, 6, 1)) == [
        date(2024, 3, 12),
        date(2024, 4, 9),
        date(2024, 5, 14),
    ]


def test_next_after_and_describe():
    rule = daily(date(2024, 3, 4), interval=7, count=4)
    assert rule.next_after(date(2024, 3, 5)) == date(2024, 3, 11)
    assert rule.describe() == "every 7 days, 4 times"
