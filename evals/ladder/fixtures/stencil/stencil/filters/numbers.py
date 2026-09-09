"""Numeric filters."""

GROUP = 3


def comma(value):
    """Group the whole part into thousands: 1234567 -> '1,234,567'."""
    number = float(value)
    sign = "-" if number < 0 else ""
    digits = str(int(abs(number)))
    groups = []
    while len(digits) > GROUP:
        groups.insert(0, digits[-GROUP:])
        digits = digits[:-GROUP]
    groups.insert(0, digits)
    return sign + ",".join(groups)


def percent(value):
    """Show a 0..1 ratio as a whole-number percentage."""
    return "%d%%" % round(float(value) * 100)


def round_to(value, places=2):
    return round(float(value), places)


def plural(value):
    """Suffix helper: `{{ n }} item{{ n|plural }}`."""
    return "" if int(value) == 1 else "s"
