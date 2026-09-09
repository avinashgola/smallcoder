"""Small helpers for walking over ranges of calendar dates."""

from datetime import date, timedelta

DAY = timedelta(days=1)


def iter_days(start, end):
    """Yield every date from *start* up to but not including *end*."""
    cursor = start
    while cursor <= end:
        yield cursor
        cursor = cursor + DAY


def day_count(start, end):
    """Number of calendar days in the half-open range [start, end)."""
    if end <= start:
        return 0
    return (end - start).days


def month_start(day):
    """First day of the month containing *day*."""
    return day.replace(day=1)


def next_month_start(day):
    """First day of the month after the one containing *day*."""
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def month_end(day):
    """Last day of the month containing *day*."""
    return next_month_start(day) - DAY


def iter_months(start, end):
    """Yield the first day of every month touched by the window [start, end]."""
    cursor = month_start(start)
    while cursor <= end:
        yield cursor
        cursor = next_month_start(cursor)


def week_start(day, first_weekday=0):
    """First day of the week containing *day*, given the week's first weekday."""
    offset = (day.weekday() - first_weekday) % 7
    return day - timedelta(days=offset)


def clamp(day, low=None, high=None):
    """Restrict *day* to the inclusive window [low, high]."""
    if low is not None and day < low:
        return low
    if high is not None and day > high:
        return high
    return day


def overlaps(start_a, end_a, start_b, end_b):
    """True when two half-open date ranges share at least one day."""
    return start_a < end_b and start_b < end_a
