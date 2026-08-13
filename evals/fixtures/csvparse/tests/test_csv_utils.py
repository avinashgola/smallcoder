from csv_utils import parse_records, total_value

CSV = """name, quantity, unit_price
widget, 2, 3.50
gadget , 1 , 10.00
 spacer, 4, 0.25
"""


def test_record_count():
    assert len(parse_records(CSV)) == 3


def test_numeric_fields_parsed():
    records = parse_records(CSV)
    assert records[0]["quantity"] == 2
    assert records[0]["unit_price"] == 3.50


def test_names_have_no_stray_whitespace():
    records = parse_records(CSV)
    assert [r["name"] for r in records] == ["widget", "gadget", "spacer"]


def test_total_value():
    assert total_value(parse_records(CSV)) == 18.00


def test_malformed_row_rejected():
    import pytest

    with pytest.raises(ValueError):
        parse_records("name, quantity, unit_price\nonly,two\n")
