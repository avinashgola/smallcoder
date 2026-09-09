"""The shapes a recurrence can take, each answering 'does this date match?'."""

from recur.spans import days_in_month, month_index, weeks_between
from recur.weekdays import parse_weekdays, weekday_name


class DailyPattern(object):
    """Every *interval* days, counted from the rule's start date."""

    def __init__(self, interval=1):
        if interval < 1:
            raise ValueError("interval must be at least 1")
        self.interval = interval

    def matches(self, start, day):
        if day < start:
            return False
        return (day - start).days % self.interval == 0

    def describe(self):
        if self.interval == 1:
            return "every day"
        return "every %d days" % self.interval


class WeeklyPattern(object):
    """Chosen weekdays, in every *interval*-th week from the start week."""

    def __init__(self, weekdays, interval=1):
        if interval < 1:
            raise ValueError("interval must be at least 1")
        self.weekdays = parse_weekdays(weekdays)
        self.interval = interval

    def matches(self, start, day):
        if day < start or day.weekday() not in self.weekdays:
            return False
        return weeks_between(start, day) % self.interval == 0

    def describe(self):
        names = ", ".join(weekday_name(index) for index in self.weekdays)
        if self.interval == 1:
            return "every week on %s" % names
        return "every %d weeks on %s" % (self.interval, names)


class MonthlyByDayPattern(object):
    """A day of the month, clamped down when the month is too short."""

    def __init__(self, day_of_month, interval=1):
        if not 1 <= day_of_month <= 31:
            raise ValueError("day of month out of range")
        self.day_of_month = day_of_month
        self.interval = interval

    def matches(self, start, day):
        if day < start:
            return False
        if (month_index(day) - month_index(start)) % self.interval != 0:
            return False
        target = min(self.day_of_month, days_in_month(day.year, day.month))
        return day.day == target

    def describe(self):
        return "day %d of every %d month(s)" % (self.day_of_month, self.interval)


class MonthlyByWeekdayPattern(object):
    """The *index*-th given weekday of the month, e.g. the second Tuesday."""

    def __init__(self, weekday, index, interval=1):
        if not 1 <= index <= 5:
            raise ValueError("weekday index out of range")
        self.weekday = parse_weekdays(weekday)[0]
        self.index = index
        self.interval = interval

    def matches(self, start, day):
        if day < start or day.weekday() != self.weekday:
            return False
        if (month_index(day) - month_index(start)) % self.interval != 0:
            return False
        return (day.day - 1) // 7 + 1 == self.index

    def describe(self):
        return "the %d%s %s of the month" % (
            self.index,
            {1: "st", 2: "nd", 3: "rd"}.get(self.index, "th"),
            weekday_name(self.weekday),
        )
