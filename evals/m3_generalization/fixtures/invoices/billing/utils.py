"""Invoice math helpers used by the billing pipeline."""


def apply_credit(total, credit):
    """Apply an account credit to an invoice total."""
    return round(total - credit, 2)


def add_late_fee(total, days_overdue, daily_fee=1.5):
    """Add the flat daily late fee for each overdue day."""
    if days_overdue <= 0:
        return round(total, 2)
    return round(total + days_overdue * daily_fee, 2)


def split_evenly(total, ways):
    """Split a total into equal shares; the last share absorbs rounding."""
    if ways < 1:
        raise ValueError("ways must be >= 1")
    share = round(total / ways, 2)
    last = round(total - share * (ways - 1), 2)
    return [share] * (ways - 1) + [last]
