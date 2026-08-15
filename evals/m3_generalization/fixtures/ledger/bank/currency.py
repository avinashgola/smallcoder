"""Currency display helpers used by the statement printer."""

SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£"}


def display(amount, code="USD"):
    symbol = SYMBOLS.get(code, code + " ")
    return f"{symbol}{amount:,.2f}"
