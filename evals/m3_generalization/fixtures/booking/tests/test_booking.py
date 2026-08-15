import pytest

from scheduling.booking import can_book, free_slots, overlaps


def test_genuine_overlap_detected():
    assert overlaps(9 * 60, 10 * 60, 9 * 60 + 30, 11 * 60)


def test_containment_detected():
    assert overlaps(9 * 60, 12 * 60, 10 * 60, 11 * 60)


def test_back_to_back_is_not_a_conflict():
    assert not overlaps(9 * 60, 10 * 60, 10 * 60, 11 * 60)


def test_can_book_back_to_back():
    existing = [(9 * 60, 10 * 60), (13 * 60, 14 * 60)]
    assert can_book(existing, 10 * 60, 11 * 60)


def test_can_book_rejects_overlap():
    existing = [(9 * 60, 10 * 60)]
    assert not can_book(existing, 9 * 60 + 45, 10 * 60 + 15)


def test_invalid_range_rejected():
    with pytest.raises(ValueError):
        can_book([], 10 * 60, 10 * 60)


def test_free_slots():
    existing = [(10 * 60, 11 * 60)]
    assert free_slots(existing, 9 * 60, 12 * 60) == [(9 * 60, 10 * 60), (11 * 60, 12 * 60)]
