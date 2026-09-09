"""Turn a number of seconds back into the text a report shows."""

from spans.arith import split
from spans.units import HOURS_PER_DAY

SUFFIXES = ("d", "h", "m", "s")
NAMES = (("day", "days"), ("hour", "hours"), ("minute", "minutes"), ("second", "seconds"))


def compact(total_seconds):
    """'1h30m' style, skipping the components that are zero."""
    if total_seconds == 0:
        return "0s"
    parts = []
    for value, suffix in zip(split(total_seconds), SUFFIXES):
        if value:
            parts.append("%d%s" % (value, suffix))
    sign = "-" if total_seconds < 0 else ""
    return sign + "".join(parts)


def clock(total_seconds):
    """'HH:MM:SS' style, with any whole days folded into the hours."""
    days, hours, minutes, seconds = split(total_seconds)
    sign = "-" if total_seconds < 0 else ""
    return "%s%02d:%02d:%02d" % (sign, hours + days * HOURS_PER_DAY, minutes, seconds)


def human(total_seconds, max_parts=2):
    """'1 hour 30 minutes' style, keeping only the largest components."""
    if total_seconds == 0:
        return "0 seconds"
    said = []
    for value, (singular, plural) in zip(split(total_seconds), NAMES):
        if value and len(said) < max_parts:
            said.append("%d %s" % (value, singular if value == 1 else plural))
    text = " ".join(said)
    return "minus " + text if total_seconds < 0 else text


def iso(total_seconds):
    """ISO 8601 form, e.g. 'P1DT2H30M'."""
    days, hours, minutes, seconds = split(total_seconds)
    date_part = "%dD" % days if days else ""
    time_part = ""
    for value, letter in ((hours, "H"), (minutes, "M"), (seconds, "S")):
        if value:
            time_part += "%d%s" % (value, letter)
    body = date_part + ("T" + time_part if time_part else "")
    if not body:
        return "PT0S"
    sign = "-" if total_seconds < 0 else ""
    return sign + "P" + body
