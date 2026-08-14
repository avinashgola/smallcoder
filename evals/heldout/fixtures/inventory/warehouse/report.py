"""Inventory reporting (presentation layer only)."""

from warehouse.stock import available, needs_reorder


def availability_report(items):
    """items: list of {'sku', 'on_hand', 'reserved'} dicts."""
    return {
        item["sku"]: available(item["on_hand"], item["reserved"]) for item in items
    }


def reorder_list(items, threshold=5):
    return sorted(
        item["sku"]
        for item in items
        if needs_reorder(item["on_hand"], item["reserved"], threshold)
    )
