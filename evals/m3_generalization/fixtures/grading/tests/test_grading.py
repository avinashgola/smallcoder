import pytest

from grading import letter_grade, passing, summary


def test_midrange_grades():
    assert letter_grade(95) == "A"
    assert letter_grade(85) == "B"
    assert letter_grade(72) == "C"
    assert letter_grade(65) == "D"
    assert letter_grade(30) == "F"


def test_exact_cutoffs_earn_the_higher_grade():
    assert letter_grade(90) == "A"
    assert letter_grade(80) == "B"
    assert letter_grade(70) == "C"
    assert letter_grade(60) == "D"


def test_out_of_range_rejected():
    with pytest.raises(ValueError):
        letter_grade(101)
    with pytest.raises(ValueError):
        letter_grade(-1)


def test_passing_filters_failures():
    assert passing([90, 59, 60, 12]) == [90, 60]


def test_summary_counts():
    assert summary([90, 91, 60, 59]) == {"A": 2, "D": 1, "F": 1}
