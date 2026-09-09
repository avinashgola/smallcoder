"""The static data the reports are built from."""

SALES = [
    {"region": "north", "quarter": "q1", "units": 120, "revenue": 14400},
    {"region": "north", "quarter": "q2", "units": 98, "revenue": 11760},
    {"region": "south", "quarter": "q1", "units": 210, "revenue": 23100},
    {"region": "south", "quarter": "q2", "units": 250, "revenue": 27500},
    {"region": "east", "quarter": "q1", "units": 64, "revenue": 8320},
    {"region": "east", "quarter": "q2", "units": 71, "revenue": 9230},
]

CATALOG = [
    {"sku": "A-100", "name": "Desk lamp", "price": 39.0, "stock": 12},
    {"sku": "A-101", "name": 'Chair, "office"', "price": 149.5, "stock": 3},
    {"sku": "B-200", "name": "Standing desk", "price": 480.0, "stock": 0},
]

QUARTERS = ("q1", "q2")
REGIONS = ("north", "south", "east")


def rows_for(region=None, quarter=None):
    """Sales rows filtered by region and quarter, in source order."""
    rows = SALES
    if region is not None:
        rows = [row for row in rows if row["region"] == region]
    if quarter is not None:
        rows = [row for row in rows if row["quarter"] == quarter]
    return [dict(row) for row in rows]


def totals(rows):
    """Aggregate units and revenue over ``rows``."""
    return {
        "units": sum(row["units"] for row in rows),
        "revenue": sum(row["revenue"] for row in rows),
        "count": len(rows),
    }
