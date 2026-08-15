from finance.amounts import parse_amount, parse_amounts, total


def test_plain_amounts():
    assert parse_amount("15.75") == 15.75
    assert parse_amount("$99") == 99.0


def test_thousands_separator_with_decimals():
    assert parse_amount("1,234.56") == 1234.56


def test_thousands_separator_without_decimals():
    assert parse_amount("2,500") == 2500.0


def test_parse_amounts_skips_blank_lines():
    assert parse_amounts(["$5", "", "10.25"]) == [5.0, 10.25]


def test_total():
    assert total(["1,000", "250.50"]) == 1250.5
