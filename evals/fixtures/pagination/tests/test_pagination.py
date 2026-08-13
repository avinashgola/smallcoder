import pytest

from pagination import paginate, total_pages

ITEMS = list(range(1, 11))  # 10 items


def test_full_page_size():
    assert paginate(ITEMS, page=1, per_page=3) == [1, 2, 3]


def test_second_page():
    assert paginate(ITEMS, page=2, per_page=3) == [4, 5, 6]


def test_last_partial_page():
    assert paginate(ITEMS, page=4, per_page=3) == [10]


def test_page_past_end_is_empty():
    assert paginate(ITEMS, page=5, per_page=3) == []


def test_single_item_pages():
    assert paginate(ITEMS, page=7, per_page=1) == [7]


def test_invalid_page_rejected():
    with pytest.raises(ValueError):
        paginate(ITEMS, page=0, per_page=3)


def test_total_pages():
    assert total_pages(10, 3) == 4
    assert total_pages(9, 3) == 3
