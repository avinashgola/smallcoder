"""Pricing helpers (unrelated to stock levels)."""

TAX_RATE = 0.08


def with_tax(amount):
    return round(amount * (1 + TAX_RATE), 2)


def bulk_price(unit_price, quantity):
    if quantity >= 100:
        return round(unit_price * quantity * 0.9, 2)
    return round(unit_price * quantity, 2)
