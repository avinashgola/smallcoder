"""Arithmetic and unit conversion on durations measured in seconds."""

from spans.units import (
    HOURS_PER_DAY,
    MINUTES_PER_HOUR,
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
)


def split(total_seconds):
    """Break a duration into (days, hours, minutes, seconds), all non negative."""
    rest = abs(int(total_seconds))
    days, rest = divmod(rest, SECONDS_PER_DAY)
    hours, rest = divmod(rest, SECONDS_PER_HOUR)
    minutes, seconds = divmod(rest, SECONDS_PER_MINUTE)
    return days, hours, minutes, seconds


def combine(days=0, hours=0, minutes=0, seconds=0):
    """The inverse of split: assemble components back into seconds."""
    return (
        days * SECONDS_PER_DAY
        + hours * SECONDS_PER_HOUR
        + minutes * SECONDS_PER_MINUTE
        + seconds
    )


def to_minutes(total_seconds, places=2):
    """Express a duration as a fractional number of minutes."""
    return round(total_seconds / SECONDS_PER_MINUTE, places)


def to_hours(total_seconds, places=2):
    """Express a duration as a fractional number of hours."""
    return round(total_seconds / SECONDS_PER_MINUTE * MINUTES_PER_HOUR, places)


def to_days(total_seconds, places=3):
    """Express a duration as a fractional number of twenty-four hour days."""
    return round(total_seconds / (SECONDS_PER_HOUR * HOURS_PER_DAY), places)


def round_up(total_seconds, increment):
    """Round a duration up onto the next whole increment."""
    if increment <= 0:
        raise ValueError("increment must be positive")
    whole, remainder = divmod(total_seconds, increment)
    return (whole + 1) * increment if remainder else whole * increment


def round_nearest(total_seconds, increment):
    """Round a duration onto the closest increment, halves going up."""
    if increment <= 0:
        raise ValueError("increment must be positive")
    whole, remainder = divmod(total_seconds, increment)
    if remainder * 2 >= increment:
        whole += 1
    return whole * increment


def clamp(total_seconds, low=None, high=None):
    """Restrict a duration to the inclusive range [low, high]."""
    if low is not None and total_seconds < low:
        return low
    if high is not None and total_seconds > high:
        return high
    return total_seconds


def scale(total_seconds, factor):
    """Multiply a duration, rounding half away from zero."""
    product = total_seconds * factor
    return int(product + 0.5) if product >= 0 else -int(-product + 0.5)
