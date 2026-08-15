from pos.receipt import receipt_lines, total_display


def test_line_item_with_cents_padding():
    lines = receipt_lines([("coffee", 1, 505)])
    assert lines[0] == "coffee x1  5.05"


def test_round_dollar_total():
    assert total_display([("bagel", 2, 600)]) == "TOTAL  12.00"


def test_no_padding_needed():
    lines = receipt_lines([("tea", 1, 555)])
    assert lines[0] == "tea x1  5.55"


def test_totals_add_up():
    lines = receipt_lines([("coffee", 2, 505), ("bagel", 1, 250)])
    assert lines[-1] == "TOTAL  12.60"
