from calendar_utils import days_in_month, days_in_year, is_leap_year


def test_ordinary_leap_years():
    assert is_leap_year(2024)
    assert is_leap_year(1996)


def test_non_leap_years():
    assert not is_leap_year(2023)
    assert not is_leap_year(1997)


def test_century_years_are_not_leap():
    assert not is_leap_year(1900)
    assert not is_leap_year(2100)


def test_four_hundred_year_rule():
    assert is_leap_year(2000)
    assert is_leap_year(1600)


def test_february_length():
    assert days_in_month(2000, 2) == 29
    assert days_in_month(1900, 2) == 28


def test_days_in_year():
    assert days_in_year(2000) == 366
    assert days_in_year(1900) == 365
