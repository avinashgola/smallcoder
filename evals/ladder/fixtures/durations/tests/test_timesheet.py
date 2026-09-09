from datetime import date

from timesheet.entries import InvalidEntry, TimeEntry, load, parse_line
from timesheet.summary import (
    billable_hours,
    billable_split,
    by_day,
    by_project,
    overtime_hours,
    project_hours,
    report_lines,
    total_hours,
    total_seconds,
)

WEEK = [
    "# week of 4 March 2024",
    "2024-03-04 | acme   | 1h30m    | billable",
    "2024-03-04 | zenith | 45m      | billable",
    "2024-03-05 | acme   | 2h       | billable",
    "",
    "2024-03-05 | admin  | 30m      | internal",
    "2024-03-06 | acme   | 01:15:00 | billable",
]


def test_loading_skips_blanks_and_comments():
    entries = load(WEEK)
    assert len(entries) == 5
    assert entries[0].project == "acme"
    assert entries[0].day == date(2024, 3, 4)
    assert entries[3].billable is False


def test_bad_lines_are_rejected():
    for line in ("2024-03-04 | acme | 1h30m", "not-a-date | acme | 1h | billable"):
        try:
            parse_line(line)
        except InvalidEntry:
            continue
        raise AssertionError("expected %r to be rejected" % (line,))


def test_entry_rounding_and_hours():
    entry = TimeEntry.from_text("acme", date(2024, 3, 6), "1h15m")
    assert entry.seconds == 4500
    assert entry.rounded(1800).seconds == 5400
    assert entry.hours() == 1.25


def test_totals_in_seconds():
    entries = load(WEEK)
    assert total_seconds(entries) == 21600
    assert by_project(entries) == [("acme", 17100), ("admin", 1800), ("zenith", 2700)]
    assert by_day(entries) == [
        (date(2024, 3, 4), 8100),
        (date(2024, 3, 5), 9000),
        (date(2024, 3, 6), 4500),
    ]
    assert billable_split(entries) == (19800, 1800)


def test_totals_in_hours():
    entries = load(WEEK)
    assert total_hours(entries) == 6.0
    assert billable_hours(entries) == 5.5
    assert project_hours(entries) == [("acme", 4.75), ("admin", 0.5), ("zenith", 0.75)]


def test_overtime_against_a_cap():
    entries = load(WEEK)
    assert overtime_hours(entries, cap_hours=1) == 5.0
    assert overtime_hours(entries) == 0.0


def test_report_lines():
    assert report_lines(load(WEEK)) == [
        "acme: 4h45m (4.75h)",
        "admin: 30m (0.5h)",
        "zenith: 45m (0.75h)",
    ]
