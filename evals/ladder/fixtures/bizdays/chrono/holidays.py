"""Holiday rules and the arithmetic that places them on a concrete date."""

from datetime import date, timedelta

from chrono.ranges import month_end

SATURDAY = 5
SUNDAY = 6


def observed_date(day):
    """Shift a holiday that lands on a weekend onto the adjacent weekday."""
    if day.weekday() == SATURDAY:
        return day - timedelta(days=1)
    if day.weekday() == SUNDAY:
        return day + timedelta(days=1)
    return day


class FixedHoliday(object):
    """A holiday on the same month and day every year."""

    def __init__(self, name, month, day, observed=True):
        self.name = name
        self.month = month
        self.day = day
        self.observed = observed

    def date_in(self, year):
        actual = date(year, self.month, self.day)
        return observed_date(actual) if self.observed else actual

    def __repr__(self):
        return "FixedHoliday(%r, %d, %d)" % (self.name, self.month, self.day)


class NthWeekdayHoliday(object):
    """A holiday such as 'the fourth Thursday in November'."""

    def __init__(self, name, month, weekday, index):
        self.name = name
        self.month = month
        self.weekday = weekday
        self.index = index

    def date_in(self, year):
        first = date(year, self.month, 1)
        offset = (self.weekday - first.weekday()) % 7
        return first + timedelta(days=offset + 7 * (self.index - 1))

    def __repr__(self):
        return "NthWeekdayHoliday(%r, %d)" % (self.name, self.index)


class LastWeekdayHoliday(object):
    """A holiday such as 'the last Monday in May'."""

    def __init__(self, name, month, weekday):
        self.name = name
        self.month = month
        self.weekday = weekday

    def date_in(self, year):
        last = month_end(date(year, self.month, 1))
        offset = (last.weekday() - self.weekday) % 7
        return last - timedelta(days=offset)

    def __repr__(self):
        return "LastWeekdayHoliday(%r)" % (self.name,)


DEFAULT_HOLIDAYS = (
    FixedHoliday("New Year's Day", 1, 1),
    NthWeekdayHoliday("Presidents' Day", 2, 0, 3),
    LastWeekdayHoliday("Memorial Day", 5, 0),
    FixedHoliday("Independence Day", 7, 4),
    NthWeekdayHoliday("Labor Day", 9, 0, 1),
    NthWeekdayHoliday("Thanksgiving", 11, 3, 4),
    FixedHoliday("Christmas Day", 12, 25),
)
