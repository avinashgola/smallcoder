from datetime import date

from worktime.reporting import capacity, monthly_working_days, utilisation, working_days_in_month


def test_working_days_in_a_plain_month():
    assert working_days_in_month(2024, 3) == 21


def test_working_days_in_a_month_with_a_holiday():
    assert working_days_in_month(2024, 7) == 22


def test_monthly_breakdown_covers_every_month_touched():
    rows = monthly_working_days(date(2024, 3, 15), date(2024, 4, 2))
    assert rows == [(date(2024, 3, 1), 21), (date(2024, 4, 1), 22)]


def test_utilisation_is_a_fraction_of_the_month():
    assert utilisation(21, 2024, 3) == 1.0
    assert utilisation(11, 2024, 3) == 0.5238


def test_capacity_scales_with_headcount():
    assert capacity(3, date(2024, 3, 1), date(2024, 3, 31)) == 63
