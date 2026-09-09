"""The business calendar: which days are working days, and arithmetic on them."""

from datetime import timedelta

from chrono.holidays import DEFAULT_HOLIDAYS
from chrono.ranges import iter_days
from chrono.weekmask import STANDARD_WEEK, describe, parse_weekmask

DAY = timedelta(days=1)


class BusinessCalendar(object):
    """Working days for one office.

    *weekmask* says which weekdays are worked, *holidays* is a sequence of
    holiday rules and *closures* is a set of one-off shutdown dates that do
    not repeat from year to year.
    """

    def __init__(self, weekmask=STANDARD_WEEK, holidays=None, closures=()):
        self.workdays = parse_weekmask(weekmask)
        self.rules = tuple(DEFAULT_HOLIDAYS if holidays is None else holidays)
        self.closures = frozenset(closures)
        self._cache = {}

    def holidays_in(self, year):
        """Map of {date: name} for every holiday observed during *year*.

        Neighbouring years are consulted too because an observed date can
        slip across a year boundary.
        """
        if year not in self._cache:
            found = {}
            for offset in (-1, 0, 1):
                for rule in self.rules:
                    day = rule.date_in(year + offset)
                    if day.year == year:
                        found[day] = rule.name
            self._cache[year] = found
        return self._cache[year]

    def holiday_name(self, day):
        """Name of the holiday or closure on *day*, or None."""
        if day in self.closures:
            return "closure"
        return self.holidays_in(day.year).get(day)

    def is_business_day(self, day):
        if day.weekday() not in self.workdays:
            return False
        return self.holiday_name(day) is None

    def next_business_day(self, day):
        """First business day strictly after *day*."""
        cursor = day + DAY
        while not self.is_business_day(cursor):
            cursor += DAY
        return cursor

    def previous_business_day(self, day):
        """Last business day strictly before *day*."""
        cursor = day - DAY
        while not self.is_business_day(cursor):
            cursor -= DAY
        return cursor

    def roll_forward(self, day):
        """*day* itself if it is worked, otherwise the next business day."""
        cursor = day
        while not self.is_business_day(cursor):
            cursor += DAY
        return cursor

    def add_business_days(self, day, count):
        """Move *count* business days forward (or backward when negative)."""
        if count == 0:
            return self.roll_forward(day)
        step = self.next_business_day if count > 0 else self.previous_business_day
        cursor = day
        for _ in range(abs(count)):
            cursor = step(cursor)
        return cursor

    def business_days_between(self, start, end):
        """Count the business days in the half-open range [start, end)."""
        if end <= start:
            return 0
        return sum(1 for day in iter_days(start, end) if self.is_business_day(day))

    def __repr__(self):
        return "BusinessCalendar(%s)" % describe(self.workdays)
