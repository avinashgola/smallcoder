"""Numeric helpers that keep the stages free of edge case noise."""


def safe_div(numerator, denominator, default=0.0):
    """Division that returns `default` instead of raising on a zero divisor."""
    if not denominator:
        return default
    return numerator / denominator


def round_to(value, places=2):
    return round(float(value), places)


def clamp(value, low, high):
    if low > high:
        raise ValueError("low bound is above the high bound")
    return max(low, min(high, value))


def total(values):
    return sum(float(value) for value in values)


def mean(values):
    values = list(values)
    return round_to(safe_div(total(values), len(values)))


def percent(part, whole, places=1):
    return round(safe_div(part * 100.0, whole), places)


def as_number(value, default=0.0):
    """Coerce a value read out of a record into a float."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default
