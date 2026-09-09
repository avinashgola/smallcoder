from datetime import date

from chrono.weekmask import WeekmaskError, describe, parse_weekmask
from worktime.business import BusinessCalendar


def test_weekmask_spellings_agree():
    assert parse_weekmask("1111100") == parse_weekmask("mon-fri")
    assert parse_weekmask("mon,wed,fri") == frozenset([0, 2, 4])
    assert describe(parse_weekmask("mon-fri")) == "mon,tue,wed,thu,fri"


def test_weekmask_rejects_nonsense():
    try:
        parse_weekmask("fri-mon")
    except WeekmaskError:
        pass
    else:
        raise AssertionError("reversed range should be rejected")


def test_weekends_and_holidays_are_not_business_days():
    cal = BusinessCalendar()
    assert cal.is_business_day(date(2024, 3, 5)) is True
    assert cal.is_business_day(date(2024, 3, 9)) is False
    assert cal.is_business_day(date(2024, 7, 4)) is False
    assert cal.holiday_name(date(2024, 11, 28)) == "Thanksgiving"
    assert cal.holiday_name(date(2024, 5, 27)) == "Memorial Day"


def test_one_off_closures_are_honoured():
    cal = BusinessCalendar(closures=[date(2024, 3, 6)])
    assert cal.is_business_day(date(2024, 3, 6)) is False
    assert cal.holiday_name(date(2024, 3, 6)) == "closure"


def test_add_business_days_skips_weekends_and_holidays():
    cal = BusinessCalendar()
    assert cal.add_business_days(date(2024, 3, 4), 3) == date(2024, 3, 7)
    assert cal.add_business_days(date(2024, 3, 8), 1) == date(2024, 3, 11)
    assert cal.add_business_days(date(2024, 7, 3), 2) == date(2024, 7, 8)
    assert cal.add_business_days(date(2024, 3, 11), -1) == date(2024, 3, 8)
    assert cal.add_business_days(date(2024, 3, 9), 0) == date(2024, 3, 11)


def test_business_days_between_is_half_open():
    cal = BusinessCalendar()
    assert cal.business_days_between(date(2024, 3, 4), date(2024, 3, 8)) == 4
    assert cal.business_days_between(date(2024, 3, 4), date(2024, 3, 11)) == 5
    assert cal.business_days_between(date(2024, 3, 4), date(2024, 3, 4)) == 0


def test_business_days_between_drops_a_holiday():
    cal = BusinessCalendar()
    assert cal.business_days_between(date(2024, 7, 1), date(2024, 7, 8)) == 4


def test_six_day_week_counts_saturdays():
    cal = BusinessCalendar(weekmask="1111110")
    assert cal.business_days_between(date(2024, 3, 4), date(2024, 3, 11)) == 6
