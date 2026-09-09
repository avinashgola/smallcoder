"""Individual logged time entries and the text form they arrive in."""

from datetime import date

from spans.arith import round_up, to_hours
from spans.parse import DurationError, parse_duration

FIELD_COUNT = 4


class InvalidEntry(ValueError):
    """Raised when a timesheet line cannot be read."""


class TimeEntry(object):
    """One block of time logged against a project on a given day."""

    def __init__(self, project, day, seconds, billable=True):
        if seconds < 0:
            raise InvalidEntry("a time entry cannot be negative")
        self.project = project
        self.day = day
        self.seconds = seconds
        self.billable = billable

    @classmethod
    def from_text(cls, project, day, text, billable=True):
        return cls(project, day, parse_duration(text), billable)

    def rounded(self, increment):
        """A copy rounded up onto the given billing increment."""
        return TimeEntry(
            self.project, self.day, round_up(self.seconds, increment), self.billable
        )

    def hours(self):
        return to_hours(self.seconds)

    def __repr__(self):
        return "TimeEntry(%r, %s, %d)" % (self.project, self.day, self.seconds)


def parse_line(line):
    """Read '2024-03-04 | acme | 1h30m | billable' into a TimeEntry."""
    parts = [part.strip() for part in line.split("|")]
    if len(parts) != FIELD_COUNT:
        raise InvalidEntry("expected %d fields: %r" % (FIELD_COUNT, line))
    day_text, project, duration_text, flag = parts
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise InvalidEntry("bad date: %r" % (day_text,))
    if not project:
        raise InvalidEntry("missing project: %r" % (line,))
    try:
        seconds = parse_duration(duration_text)
    except DurationError:
        raise InvalidEntry("bad duration: %r" % (duration_text,))
    return TimeEntry(project, day, seconds, flag.lower() != "internal")


def load(lines):
    """Parse every line that is not blank or a comment."""
    entries = []
    for line in lines:
        text = line.strip()
        if text and not text.startswith("#"):
            entries.append(parse_line(text))
    return entries
