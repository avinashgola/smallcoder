"""Named events driven by a recurrence rule, and the agenda that merges them."""


class EventSeries(object):
    """One titled event and the rule that says when it happens."""

    def __init__(self, title, rule):
        self.title = title
        self.rule = rule

    def cancel(self, day):
        """Drop a single occurrence of this series without touching the rest."""
        self.rule.exclude(day)
        return self

    def occurrences_between(self, window_start, window_end):
        return self.rule.between(window_start, window_end)

    def next_after(self, day):
        return self.rule.next_after(day)

    def describe(self):
        return "%s: %s" % (self.title, self.rule.describe())

    def __repr__(self):
        return "EventSeries(%r)" % (self.title,)


class Agenda(object):
    """Several series merged into one chronological list of entries."""

    def __init__(self, series=()):
        self.series = list(series)

    def add(self, series):
        self.series.append(series)
        return self

    def entries_between(self, window_start, window_end):
        """[(date, title), ...] sorted by date and then by title."""
        rows = []
        for item in self.series:
            for day in item.occurrences_between(window_start, window_end):
                rows.append((day, item.title))
        rows.sort()
        return rows

    def days_with_entries(self, window_start, window_end):
        seen = []
        for day, _ in self.entries_between(window_start, window_end):
            if day not in seen:
                seen.append(day)
        return seen

    def busiest_day(self, window_start, window_end):
        """The day carrying the most entries; ties go to the earliest date."""
        counts = {}
        for day, _ in self.entries_between(window_start, window_end):
            counts[day] = counts.get(day, 0) + 1
        if not counts:
            return None
        return max(sorted(counts), key=lambda day: counts[day])
