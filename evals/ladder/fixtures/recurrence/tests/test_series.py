from datetime import date

from agenda.digest import (
    busiest_weekday,
    count_in,
    first_n,
    gaps,
    group_by_month,
    group_by_week,
    merge,
    render_weekly_digest,
)
from agenda.series import Agenda, EventSeries
from recur.rules import daily, monthly_on_weekday, weekly


def make_agenda():
    standup = EventSeries("Standup", weekly(date(2024, 3, 4), "mo,tu,we,th,fr"))
    retro = EventSeries("Retro", weekly(date(2024, 3, 4), "fr"))
    board = EventSeries("Board", monthly_on_weekday(date(2024, 3, 1), "tu", 2))
    return Agenda([standup, retro, board])


def test_expansion_helpers():
    rule = daily(date(2024, 3, 4), interval=3)
    taken = first_n(rule, 4)
    assert taken[-1] == date(2024, 3, 13)
    assert gaps(taken) == [3, 3, 3]
    assert count_in(rule, date(2024, 3, 4), date(2024, 3, 14)) == 4
    pairs = merge([rule, weekly(date(2024, 3, 4), "tu")], date(2024, 3, 4), date(2024, 3, 8))
    assert [day for day, _ in pairs] == [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 7)]


def test_agenda_merges_series_in_date_order():
    entries = make_agenda().entries_between(date(2024, 3, 6), date(2024, 3, 9))
    assert entries == [
        (date(2024, 3, 6), "Standup"),
        (date(2024, 3, 7), "Standup"),
        (date(2024, 3, 8), "Retro"),
        (date(2024, 3, 8), "Standup"),
    ]


def test_busiest_day_prefers_the_earliest_tie():
    agenda = make_agenda()
    assert agenda.busiest_day(date(2024, 3, 4), date(2024, 3, 9)) == date(2024, 3, 8)
    assert agenda.days_with_entries(date(2024, 3, 4), date(2024, 3, 6)) == [
        date(2024, 3, 4),
        date(2024, 3, 5),
    ]


def test_digest_grouping():
    entries = make_agenda().entries_between(date(2024, 3, 4), date(2024, 3, 20))
    assert [monday for monday, _ in group_by_week(entries)] == [
        date(2024, 3, 4),
        date(2024, 3, 11),
        date(2024, 3, 18),
    ]
    assert [first for first, _ in group_by_month(entries)] == [date(2024, 3, 1)]
    assert busiest_weekday(entries) == "Tuesday"


def test_weekly_digest_lines():
    agenda = Agenda([EventSeries("Retro", weekly(date(2024, 3, 4), "fr"))])
    lines = render_weekly_digest(agenda, date(2024, 3, 4), date(2024, 3, 18))
    assert lines == ["2024-03-04: Retro", "2024-03-11: Retro"]


def test_cancelling_one_series_leaves_the_others_alone():
    standup = EventSeries("Standup", weekly(date(2024, 3, 4), "mo,tu,we,th,fr"))
    retro = EventSeries("Retro", weekly(date(2024, 3, 4), "fr"))
    standup.cancel(date(2024, 3, 8))
    assert standup.occurrences_between(date(2024, 3, 7), date(2024, 3, 11)) == [
        date(2024, 3, 7)
    ]
    assert retro.occurrences_between(date(2024, 3, 4), date(2024, 3, 11)) == [
        date(2024, 3, 8)
    ]


def test_a_cancellation_does_not_leak_into_a_later_series():
    cancelled = weekly(date(2024, 3, 4), "mo,we,fr", count=3)
    cancelled.exclude(date(2024, 3, 6))
    fresh = weekly(date(2024, 3, 4), "mo,we,fr", count=3)
    assert list(fresh.occurrences()) == [
        date(2024, 3, 4),
        date(2024, 3, 6),
        date(2024, 3, 8),
    ]
