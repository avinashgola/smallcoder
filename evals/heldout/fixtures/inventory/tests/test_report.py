from warehouse.report import availability_report, reorder_list

ITEMS = [
    {"sku": "AAA", "on_hand": 10, "reserved": 4},
    {"sku": "BBB", "on_hand": 3, "reserved": 0},
    {"sku": "CCC", "on_hand": 20, "reserved": 20},
]


def test_availability_subtracts_reserved():
    report = availability_report(ITEMS)
    assert report["AAA"] == 6
    assert report["BBB"] == 3
    assert report["CCC"] == 0


def test_reorder_list():
    assert reorder_list(ITEMS, threshold=5) == ["BBB", "CCC"]


def test_fully_reserved_item_is_unavailable():
    assert availability_report([{"sku": "X", "on_hand": 5, "reserved": 5}])["X"] == 0
