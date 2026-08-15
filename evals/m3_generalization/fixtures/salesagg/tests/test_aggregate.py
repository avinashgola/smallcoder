from analytics.aggregate import best_region, grand_total, region_totals


def test_single_sale_per_region():
    assert region_totals([("north", 100), ("south", 70)]) == {"north": 100.0, "south": 70.0}


def test_repeat_sales_accumulate():
    rows = [("north", 100), ("north", 50), ("south", 70)]
    assert region_totals(rows) == {"north": 150.0, "south": 70.0}


def test_best_region_uses_totals():
    rows = [("east", 80), ("west", 60), ("west", 45)]
    assert best_region(rows) == "west"


def test_grand_total():
    rows = [("north", 10.5), ("north", 4.5), ("south", 5)]
    assert grand_total(rows) == 20.0


def test_empty_rows():
    assert region_totals([]) == {}
    assert best_region([]) is None
