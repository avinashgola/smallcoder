from store.cart import Cart


def make_cart():
    cart = Cart()
    cart.add("widget", 25.00, 2)  # 50.00
    cart.add("gadget", 10.00, 5)  # 50.00
    return cart


def test_subtotal():
    assert make_cart().subtotal() == 100.00


def test_total_without_discount():
    assert make_cart().total() == 100.00


def test_total_with_ten_percent_discount():
    assert make_cart().total(discount_percent=10) == 90.00


def test_total_with_twenty_five_percent_discount():
    cart = Cart()
    cart.add("doodad", 40.00, 2)  # 80.00
    assert cart.total(discount_percent=25) == 60.00
