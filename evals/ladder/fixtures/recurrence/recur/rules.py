"""A recurrence rule: one pattern, plus the limits and cancellations on it."""

from datetime import timedelta

from recur.patterns import (
    DailyPattern,
    MonthlyByDayPattern,
    MonthlyByWeekdayPattern,
    WeeklyPattern,
)

DAY = timedelta(days=1)
MAX_SPAN_DAYS = 3660


class RecurrenceRule(object):
    """A pattern anchored at *start*, optionally capped by count or until.

    Dates listed in *exclusions* are cancelled: they are skipped without
    being charged against the occurrence count.
    """

    def __init__(self, pattern, start, count=None, until=None, exclusions=[]):
        self.pattern = pattern
        self.start = start
        self.count = count
        self.until = until
        self.exclusions = exclusions

    def exclude(self, day):
        """Cancel a single occurrence of this rule."""
        if day not in self.exclusions:
            self.exclusions.append(day)
        return self

    def is_excluded(self, day):
        return day in self.exclusions

    def _horizon(self, horizon):
        stop = self.until
        if horizon is not None and (stop is None or horizon < stop):
            stop = horizon
        if stop is None:
            if self.count is None:
                raise ValueError("an open ended rule needs a count, an until or a horizon")
            stop = self.start + timedelta(days=MAX_SPAN_DAYS)
        return stop

    def _candidates(self, stop):
        day = self.start
        while day <= stop:
            if self.pattern.matches(self.start, day):
                yield day
            day = day + DAY

    def occurrences(self, horizon=None):
        """Yield occurrence dates in order, honouring count, until and exclusions."""
        emitted = 0
        for day in self._candidates(self._horizon(horizon)):
            if self.is_excluded(day):
                continue
            yield day
            emitted += 1
            if self.count is not None and emitted >= self.count:
                return

    def between(self, window_start, window_end):
        """Occurrences inside the half-open window [window_start, window_end)."""
        horizon = window_end - DAY
        return [day for day in self.occurrences(horizon) if day >= window_start]

    def next_after(self, day, search_days=MAX_SPAN_DAYS):
        """First occurrence strictly after *day*, or None within the search span."""
        for occurrence in self.occurrences(day + timedelta(days=search_days)):
            if occurrence > day:
                return occurrence
        return None

    def describe(self):
        text = self.pattern.describe()
        if self.count is not None:
            text += ", %d times" % self.count
        if self.until is not None:
            text += ", until %s" % self.until.isoformat()
        return text


def daily(start, interval=1, count=None, until=None):
    return RecurrenceRule(DailyPattern(interval), start, count=count, until=until)


def weekly(start, weekdays, interval=1, count=None, until=None):
    pattern = WeeklyPattern(weekdays, interval)
    return RecurrenceRule(pattern, start, count=count, until=until)


def monthly_on_day(start, day_of_month, interval=1, count=None, until=None):
    pattern = MonthlyByDayPattern(day_of_month, interval)
    return RecurrenceRule(pattern, start, count=count, until=until)


def monthly_on_weekday(start, weekday, index, interval=1, count=None, until=None):
    pattern = MonthlyByWeekdayPattern(weekday, index, interval)
    return RecurrenceRule(pattern, start, count=count, until=until)
