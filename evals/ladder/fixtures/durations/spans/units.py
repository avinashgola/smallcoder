"""Unit sizes and the spellings people type for them."""

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7

SECONDS_PER_HOUR = SECONDS_PER_MINUTE * MINUTES_PER_HOUR
SECONDS_PER_DAY = SECONDS_PER_HOUR * HOURS_PER_DAY
SECONDS_PER_WEEK = SECONDS_PER_DAY * DAYS_PER_WEEK

ORDERED_UNITS = ("w", "d", "h", "m", "s")

UNIT_SECONDS = {
    "w": SECONDS_PER_WEEK,
    "d": SECONDS_PER_DAY,
    "h": SECONDS_PER_HOUR,
    "m": SECONDS_PER_MINUTE,
    "s": 1,
}

ALIASES = {
    "week": "w",
    "weeks": "w",
    "wk": "w",
    "wks": "w",
    "day": "d",
    "days": "d",
    "hour": "h",
    "hours": "h",
    "hr": "h",
    "hrs": "h",
    "minute": "m",
    "minutes": "m",
    "min": "m",
    "mins": "m",
    "second": "s",
    "seconds": "s",
    "sec": "s",
    "secs": "s",
}


class UnitError(ValueError):
    """Raised when a duration unit cannot be recognised."""


def normalise_unit(token):
    """Return the canonical single letter for a unit spelling."""
    key = str(token).strip().lower()
    key = ALIASES.get(key, key)
    if key not in UNIT_SECONDS:
        raise UnitError("unknown duration unit: %r" % (token,))
    return key


def unit_seconds(token):
    """How many seconds one of the given unit is worth."""
    return UNIT_SECONDS[normalise_unit(token)]
