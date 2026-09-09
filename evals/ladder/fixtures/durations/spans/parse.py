"""Read the duration spellings people actually type."""

import re

from spans.units import SECONDS_PER_MINUTE, unit_seconds

COMPACT_TOKEN = re.compile(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)")
ISO_FORM = re.compile(
    r"^(?P<sign>[+-])?P"
    r"(?:(?P<weeks>\d+(?:\.\d+)?)W)?"
    r"(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$"
)


class DurationError(ValueError):
    """Raised when a duration string cannot be read."""


def parse_compact(text):
    """Read '1h30m', '2d 4h' or '90 min' into seconds."""
    matches = COMPACT_TOKEN.findall(text)
    leftover = COMPACT_TOKEN.sub("", text).strip()
    if not matches or leftover:
        raise DurationError("cannot read duration: %r" % (text,))
    total = 0.0
    for value, unit in matches:
        total += float(value) * unit_seconds(unit)
    return int(round(total))


def parse_clock(text):
    """Read 'MM:SS' or 'HH:MM:SS' into seconds."""
    parts = text.strip().split(":")
    if len(parts) not in (2, 3):
        raise DurationError("cannot read clock duration: %r" % (text,))
    total = 0
    for part in parts:
        if not part.isdigit():
            raise DurationError("cannot read clock duration: %r" % (text,))
        total = total * SECONDS_PER_MINUTE + int(part)
    return total


def parse_iso(text):
    """Read an ISO 8601 duration such as 'P1DT2H30M' into seconds."""
    match = ISO_FORM.match(text.strip())
    if match is None or match.group(0) in ("P", "-P", "+P"):
        raise DurationError("cannot read ISO duration: %r" % (text,))
    fields = match.groupdict()
    total = 0.0
    for name, unit in (
        ("weeks", "w"),
        ("days", "d"),
        ("hours", "h"),
        ("minutes", "m"),
        ("seconds", "s"),
    ):
        if fields[name] is not None:
            total += float(fields[name]) * unit_seconds(unit)
    seconds = int(round(total))
    return -seconds if fields["sign"] == "-" else seconds


def parse_duration(text):
    """Read any supported duration spelling into whole seconds."""
    if isinstance(text, int):
        return text
    stripped = text.strip()
    if not stripped:
        raise DurationError("empty duration")
    negative = stripped.startswith("-") and not stripped[1:2].isalpha()
    body = stripped[1:].strip() if stripped[0] in "+-" else stripped
    if body[:1].upper() == "P":
        return parse_iso(stripped)
    if ":" in body:
        value = parse_clock(body)
    elif body.replace(".", "", 1).isdigit():
        value = int(round(float(body)))
    else:
        value = parse_compact(body)
    return -value if negative else value
