from warehouse.pricing import bulk_price, with_tax


def test_with_tax():
    assert with_tax(100.00) == 108.00


def test_bulk_discount():
    assert bulk_price(2.00, 100) == 180.00
    assert bulk_price(2.00, 10) == 20.00
