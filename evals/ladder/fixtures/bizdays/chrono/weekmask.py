"""Parsing and lookup for the set of weekdays a calendar treats as work."""

WEEKDAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

STANDARD_WEEK = "1111100"
SIX_DAY_WEEK = "1111110"
EVERY_DAY = "1111111"


class WeekmaskError(ValueError):
    """Raised when a weekmask string cannot be understood."""


def weekday_index(name):
    """Map a weekday name or abbreviation onto Monday=0 .. Sunday=6."""
    key = name.strip().lower()[:3]
    if key not in WEEKDAY_NAMES:
        raise WeekmaskError("unknown weekday %r" % (name,))
    return WEEKDAY_NAMES.index(key)


def parse_weekmask(mask):
    """Return the set of weekday numbers a mask allows.

    Three spellings are accepted: a seven character bitmask ("1111100"),
    a comma separated list ("mon,tue,thu") or an inclusive range
    ("mon-fri").  An already parsed set is passed straight through.
    """
    if isinstance(mask, (set, frozenset)):
        return frozenset(mask)
    text = mask.strip().lower()
    if len(text) == 7 and set(text) <= {"0", "1"}:
        days = frozenset(i for i, flag in enumerate(text) if flag == "1")
    elif "-" in text:
        first, _, last = text.partition("-")
        low = weekday_index(first)
        high = weekday_index(last)
        if high < low:
            raise WeekmaskError("reversed weekday range %r" % (mask,))
        days = frozenset(range(low, high + 1))
    else:
        days = frozenset(weekday_index(part) for part in text.split(",") if part.strip())
    if not days:
        raise WeekmaskError("weekmask %r selects no days" % (mask,))
    return days


def describe(workdays):
    """Human readable form of a parsed weekmask, in weekday order."""
    return ",".join(WEEKDAY_NAMES[index] for index in sorted(workdays))
