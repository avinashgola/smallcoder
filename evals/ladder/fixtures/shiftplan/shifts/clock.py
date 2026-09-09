"""Times of day held as whole minutes past midnight."""

MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY


class ClockError(ValueError):
    """Raised when a time of day cannot be read."""


def parse_time(text):
    """Read 'HH:MM' into minutes past midnight."""
    parts = str(text).strip().split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ClockError("cannot read time of day: %r" % (text,))
    hours, minutes = int(parts[0]), int(parts[1])
    if hours >= HOURS_PER_DAY or minutes >= MINUTES_PER_HOUR:
        raise ClockError("time of day out of range: %r" % (text,))
    return hours * MINUTES_PER_HOUR + minutes


def format_time(minute_of_day):
    """The 'HH:MM' form of a minute past midnight, wrapping at 24 hours."""
    return "%02d:%02d" % divmod(minute_of_day % MINUTES_PER_DAY, MINUTES_PER_HOUR)


def format_span(minutes):
    """A length of time as '8h' or '7h30m'."""
    hours, rest = divmod(minutes, MINUTES_PER_HOUR)
    return "%dh%02dm" % (hours, rest) if rest else "%dh" % hours
