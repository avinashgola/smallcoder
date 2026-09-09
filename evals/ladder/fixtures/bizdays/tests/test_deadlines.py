from datetime import date

from worktime.deadlines import SlaPolicy


def test_due_date_counts_business_days():
    policy = SlaPolicy()
    assert policy.due_date(date(2024, 3, 4), "normal") == date(2024, 3, 11)
    assert policy.due_date(date(2024, 7, 1), "high") == date(2024, 7, 3)
    assert policy.due_date(date(2024, 7, 3), "urgent") == date(2024, 7, 5)


def test_unknown_priority_is_rejected():
    policy = SlaPolicy()
    try:
        policy.due_date(date(2024, 3, 4), "whenever")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown priority should raise")


def test_overdue_flag():
    policy = SlaPolicy()
    assert policy.is_overdue(date(2024, 3, 4), "normal", date(2024, 3, 12)) is True
    assert policy.is_overdue(date(2024, 3, 4), "normal", date(2024, 3, 11)) is False


def test_days_remaining():
    policy = SlaPolicy()
    assert policy.days_remaining(date(2024, 3, 4), "normal", date(2024, 3, 6)) == 3
    assert policy.days_remaining(date(2024, 3, 4), "normal", date(2024, 3, 13)) == -2


def test_triage_splits_the_queue():
    policy = SlaPolicy()
    tickets = {
        "T-1": (date(2024, 2, 26), "normal"),
        "T-2": (date(2024, 3, 11), "low"),
        "T-3": (date(2024, 3, 11), "urgent"),
    }
    overdue, on_track = policy.triage(tickets, date(2024, 3, 13))
    assert overdue == ["T-1", "T-3"]
    assert on_track == ["T-2"]
