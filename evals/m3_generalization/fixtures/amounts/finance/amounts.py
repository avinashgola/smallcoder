"""Parse human-entered money amounts like '1,234.56' or '$99'."""


def parse_amount(text):
    """Return the numeric value of one user-entered amount string."""
    cleaned = text.strip().lstrip("$").strip()
    cleaned = cleaned.replace(",", ".")
    return round(float(cleaned), 2)


def parse_amounts(lines):
    """Parse every non-blank line into an amount."""
    return [parse_amount(line) for line in lines if line.strip()]


def total(lines):
    """Sum of all amounts in the input lines."""
    return round(sum(parse_amounts(lines)), 2)
