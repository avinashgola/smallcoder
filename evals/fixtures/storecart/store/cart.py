"""Shopping cart."""

from store.discounts import apply_discount


class Cart:
    def __init__(self):
        self._items = []

    def add(self, name, unit_price, quantity=1):
        if unit_price < 0 or quantity < 1:
            raise ValueError("invalid price or quantity")
        self._items.append((name, unit_price, quantity))

    def subtotal(self):
        return round(sum(price * qty for _, price, qty in self._items), 2)

    def total(self, discount_percent=0):
        """Cart total after applying the given percentage discount."""
        return apply_discount(self.subtotal(), discount_percent)
