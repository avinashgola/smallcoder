"""Cash-drawer session tracking for the register."""


class Drawer:
    def __init__(self, opening_cents=0):
        self.opening_cents = opening_cents
        self.sales_cents = 0

    def ring_up(self, cents):
        self.sales_cents += cents

    def expected_cents(self):
        return self.opening_cents + self.sales_cents
