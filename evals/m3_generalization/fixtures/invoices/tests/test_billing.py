from billing.utils import add_late_fee, apply_credit, split_evenly
from reports.utils import format_percent


def test_partial_credit():
    assert apply_credit(100.0, 30.0) == 70.0


def test_credit_larger_than_invoice_clamps_to_zero():
    assert apply_credit(30.0, 50.0) == 0.0


def test_exact_credit():
    assert apply_credit(25.0, 25.0) == 0.0


def test_late_fee():
    assert add_late_fee(100.0, 4) == 106.0
    assert add_late_fee(100.0, 0) == 100.0


def test_split_evenly_preserves_total():
    assert split_evenly(100.0, 3) == [33.33, 33.33, 33.34]


def test_report_formatting_helper():
    assert format_percent(0.125) == "12.5%"
