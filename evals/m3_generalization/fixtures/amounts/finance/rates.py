"""Static exchange rates for reporting (updated manually each quarter)."""

RATES = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}


def to_usd(amount, code):
    if code not in RATES:
        raise KeyError(f"no rate for {code}")
    return round(amount * RATES[code], 2)
