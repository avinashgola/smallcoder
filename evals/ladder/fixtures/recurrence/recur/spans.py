"""Month and week arithmetic that the recurrence patterns lean on."""

from datetime import date, timedelta

DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year, month):
    if month == 2 and is_leap_year(year):
        return 29
    return DAYS_IN_MONTH[month - 1]


def month_index(day):
    """Absolute month number, so two months can simply be subtracted."""
    return day.year * 12 + (day.month - 1)


def add_months(day, months):
    """Shift a date by whole months, clamping onto short months."""
    total = month_index(day) + months
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, min(day.day, days_in_month(year, month)))


def last_day_of_month(day):
    return day.replace(day=days_in_month(day.year, day.month))


def week_start(day, first_weekday=0):
    """First day of the week containing *day*."""
    return day - timedelta(days=(day.weekday() - first_weekday) % 7)


def weeks_between(earlier, later, first_weekday=0):
    """Whole weeks from the week of *earlier* to the week of *later*."""
    delta = week_start(later, first_weekday) - week_start(earlier, first_weekday)
    return delta.days // 7
