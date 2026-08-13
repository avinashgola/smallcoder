"""Product catalog helpers (not involved in the discount bug)."""

PRICES = {
    "widget": 25.00,
    "gadget": 10.00,
    "doodad": 5.50,
}


def price_of(name):
    if name not in PRICES:
        raise KeyError(f"unknown product: {name}")
    return PRICES[name]


def in_catalog(name):
    return name in PRICES
