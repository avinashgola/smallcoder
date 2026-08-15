"""A minimal single-account transaction ledger."""


class Ledger:
    def __init__(self, entries=[]):
        self.entries = entries

    def record(self, description, amount):
        """Record one transaction; positive deposits, negative withdrawals."""
        self.entries.append((description, round(float(amount), 2)))

    def balance(self):
        """Current balance across all recorded transactions."""
        return round(sum(amount for _, amount in self.entries), 2)

    def history(self):
        """All transactions in recording order."""
        return list(self.entries)
