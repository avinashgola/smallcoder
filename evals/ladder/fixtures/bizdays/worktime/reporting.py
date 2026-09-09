"""Aggregate working-day counts for capacity and utilisation reports."""

from datetime import date

from chrono.ranges import iter_months, next_month_start
from worktime.business import BusinessCalendar


def working_days_in_month(year, month, calendar=None):
    """How many working days the given month contains."""
    cal = calendar or BusinessCalendar()
    first = date(year, month, 1)
    return cal.business_days_between(first, next_month_start(first))


def monthly_working_days(start, end, calendar=None):
    """[(first-of-month, working days), ...] for every month the window touches."""
    cal = calendar or BusinessCalendar()
    rows = []
    for first in iter_months(start, end):
        rows.append((first, working_days_in_month(first.year, first.month, cal)))
    return rows


def utilisation(logged_days, year, month, calendar=None):
    """Fraction of the month's working days that were actually logged."""
    available = working_days_in_month(year, month, calendar)
    if available == 0:
        return 0.0
    return round(float(logged_days) / available, 4)


def capacity(headcount, start, end, calendar=None):
    """Total person-days available across the months a window touches."""
    return headcount * sum(count for _, count in monthly_working_days(start, end, calendar))
