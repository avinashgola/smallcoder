"""Roll logged entries up into the numbers a weekly report shows."""

from spans.arith import to_hours
from spans.render import compact
from spans.units import SECONDS_PER_HOUR

DEFAULT_WEEKLY_CAP_HOURS = 40


def total_seconds(entries):
    return sum(entry.seconds for entry in entries)


def by_project(entries):
    """[(project, seconds), ...] ordered by project name."""
    totals = {}
    for entry in entries:
        totals[entry.project] = totals.get(entry.project, 0) + entry.seconds
    return [(name, totals[name]) for name in sorted(totals)]


def by_day(entries):
    """[(date, seconds), ...] in date order."""
    totals = {}
    for entry in entries:
        totals[entry.day] = totals.get(entry.day, 0) + entry.seconds
    return [(day, totals[day]) for day in sorted(totals)]


def project_hours(entries):
    """[(project, fractional hours), ...] ordered by project name."""
    return [(name, to_hours(seconds)) for name, seconds in by_project(entries)]


def total_hours(entries):
    return to_hours(total_seconds(entries))


def billable_split(entries):
    """(billable seconds, internal seconds)."""
    billable = sum(entry.seconds for entry in entries if entry.billable)
    return billable, total_seconds(entries) - billable


def billable_hours(entries):
    return to_hours(billable_split(entries)[0])


def overtime_hours(entries, cap_hours=DEFAULT_WEEKLY_CAP_HOURS):
    """Hours logged beyond the weekly cap, or zero when under it."""
    over = total_seconds(entries) - cap_hours * SECONDS_PER_HOUR
    return to_hours(over) if over > 0 else 0.0


def report_lines(entries):
    """One 'project: 1h30m (1.5h)' line per project."""
    return [
        "%s: %s (%sh)" % (name, compact(seconds), to_hours(seconds))
        for name, seconds in by_project(entries)
    ]
