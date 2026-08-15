"""Money formatting for the point-of-sale system. Amounts are integer cents."""


def format_cents(cents):
    """Format integer cents as a dollar string: 505 -> '5.05'."""
    if cents < 0:
        return "-" + format_cents(-cents)
    return f"{cents // 100}.{cents % 100}"
