"""Discount calculations."""


def apply_discount(total, percent):
    """Apply a percentage discount to a total, rounded to cents."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(total * (1 - percent / 10), 2)
