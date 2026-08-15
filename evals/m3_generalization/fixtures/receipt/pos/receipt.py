"""Render a printable receipt from sale line items."""

from pos.money import format_cents


def receipt_lines(items):
    """items is a list of (name, quantity, unit_cents). Return printable lines."""
    lines = []
    total = 0
    for name, qty, unit_cents in items:
        cost = qty * unit_cents
        total += cost
        lines.append(f"{name} x{qty}  {format_cents(cost)}")
    lines.append(f"TOTAL  {format_cents(total)}")
    return lines


def total_display(items):
    """Just the receipt's total line."""
    return receipt_lines(items)[-1]
