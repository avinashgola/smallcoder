"""Minimal CSV record parsing (no external dependencies)."""


def parse_records(text):
    """Parse 'name,quantity,unit_price' CSV text (with a header row) into dicts."""
    records = []
    lines = [line for line in text.splitlines() if line.strip()]
    for line in lines[1:]:
        fields = line.split(",")
        if len(fields) != 3:
            raise ValueError(f"expected 3 fields, got {len(fields)}: {line!r}")
        name, quantity, unit_price = fields
        records.append(
            {"name": name, "quantity": int(quantity), "unit_price": float(unit_price)}
        )
    return records


def total_value(records):
    """Total inventory value across records, rounded to cents."""
    return round(sum(r["quantity"] * r["unit_price"] for r in records), 2)
