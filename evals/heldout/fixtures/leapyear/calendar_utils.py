"""Calendar helpers."""

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap_year(year):
    """True when `year` is a leap year in the Gregorian calendar."""
    return year % 4 == 0 and year % 100 != 0


def days_in_month(year, month):
    """Number of days in the given month, accounting for leap years."""
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if month == 2 and is_leap_year(year):
        return 29
    return DAYS_IN_MONTH[month - 1]


def days_in_year(year):
    return 366 if is_leap_year(year) else 365
