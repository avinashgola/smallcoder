"""Aggregate raw sales rows into per-region figures."""


def region_totals(rows):
    """rows is an iterable of (region, amount). Return region -> total."""
    totals = {}
    for region, amount in rows:
        totals[region] = round(float(amount), 2)
    return totals


def best_region(rows):
    """The region with the highest total, or None with no sales."""
    totals = region_totals(rows)
    if not totals:
        return None
    return max(totals, key=lambda region: totals[region])


def grand_total(rows):
    """Company-wide total across every region."""
    return round(sum(region_totals(rows).values()), 2)
