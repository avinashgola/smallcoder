"""Weekday names and the parsing of weekday selections."""

ABBREVIATIONS = ("mo", "tu", "we", "th", "fr", "sa", "su")
FULL_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

class WeekdayError(ValueError):
    """Raised when a weekday selection cannot be understood."""


def parse_weekday(token):
    """Accept 'mo', 'Mon', 'monday' or an integer and return Monday=0 .. Sunday=6."""
    if isinstance(token, int):
        if 0 <= token <= 6:
            return token
        raise WeekdayError("weekday out of range: %r" % (token,))
    key = str(token).strip().lower()[:2]
    if key not in ABBREVIATIONS:
        raise WeekdayError("unknown weekday: %r" % (token,))
    return ABBREVIATIONS.index(key)


def parse_weekdays(spec):
    """Normalise a weekday selection into a sorted tuple of weekday numbers.

    Accepts a comma separated string ("mo,we,fr"), any iterable of names or
    numbers, or a single weekday.
    """
    if isinstance(spec, int):
        return (parse_weekday(spec),)
    if isinstance(spec, str):
        parts = [part for part in spec.split(",") if part.strip()]
    else:
        parts = list(spec)
    if not parts:
        raise WeekdayError("no weekdays selected")
    return tuple(sorted({parse_weekday(part) for part in parts}))


def weekday_name(index):
    return FULL_NAMES[index]
