from rota.assignments import load
from rota.rules import Policy, consecutive_days, rest_gaps, violations, weekly_minutes


def shifts_for(rota, name):
    return [item for item in rota if item.person == name]


def test_rest_gaps_between_consecutive_shifts(rota):
    gaps = [minutes for _, _, minutes in rest_gaps(shifts_for(rota, "ben"))]
    assert gaps == [480, 960]


def test_weekly_minutes_by_iso_week(rota):
    assert weekly_minutes(shifts_for(rota, "ana")) == [
        ("2024-W10", 2400),
        ("2024-W11", 1920),
    ]
    assert weekly_minutes(shifts_for(rota, "cara")) == [("2024-W10", 480)]


def test_consecutive_days_finds_the_longest_run(rota):
    assert consecutive_days(rota) == [("ana", 7), ("ben", 3), ("cara", 1)]


def test_default_policy_violations(rota):
    assert violations(rota) == [
        "ana: 0 minutes rest between 2024-03-08 and 2024-03-09 (minimum 660)",
        "ana: 7 consecutive days rostered (maximum 6)",
        "ben: 480 minutes rest between 2024-03-04 and 2024-03-05 (minimum 660)",
    ]


def test_weekly_cap_on_its_own(rota):
    relaxed = Policy(min_rest_minutes=0, max_consecutive_days=31, max_weekly_minutes=2000)
    assert violations(rota, relaxed) == [
        "ana: 2400 minutes in 2024-W10 (maximum 2000)"
    ]


def test_a_clean_week_reports_nothing():
    clean = load(
        [
            "2024-03-04 | dev | early",
            "2024-03-05 | dev | early",
            "2024-03-06 | dev | early",
            "2024-03-07 | dev | early",
            "2024-03-08 | dev | early",
        ]
    )
    assert violations(clean) == []
    assert consecutive_days(clean) == [("dev", 5)]
