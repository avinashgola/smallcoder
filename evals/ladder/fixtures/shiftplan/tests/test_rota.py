from datetime import date

from rota.assignments import Assignment, RotaError, by_person, clashes, load, parse_line
from rota.coverage import coverage_at, coverage_spans, gap_report, understaffed


def test_loading_skips_blanks_and_comments(rota):
    assert len(rota) == 13
    assert rota[0].person == "ana"
    assert rota[0].name == "early"
    assert rota[2].window.crosses_midnight is True


def test_bad_lines_are_rejected():
    for line in ("2024-03-04 | ana", "not-a-date | ana | early", "2024-03-04 | ana | brunch"):
        try:
            parse_line(line)
        except RotaError:
            continue
        raise AssertionError("expected %r to be rejected" % (line,))


def test_grouping_is_by_name_then_start(rota):
    grouped = by_person(rota)
    assert [name for name, _ in grouped] == ["ana", "ben", "cara"]
    assert [len(shifts) for _, shifts in grouped] == [9, 3, 1]
    assert grouped[1][1][0].name == "late"


def test_a_night_shift_touching_the_next_early_is_not_a_clash(rota):
    assert clashes(rota) == []
    pairs = clashes(rota + [Assignment("ana", date(2024, 3, 9), "half")])
    assert len(pairs) == 1
    assert sorted(shift.name for shift in pairs[0]) == ["early", "half"]


def test_coverage_across_a_day(rota):
    assert coverage_spans(rota, date(2024, 3, 5)) == [
        (0, 360, 1),
        (360, 840, 2),
        (840, 1440, 0),
    ]
    assert coverage_at(rota, date(2024, 3, 5), 300) == 1
    assert coverage_at(rota, date(2024, 3, 5), 600) == 2
    assert coverage_at(rota, date(2024, 3, 5), 900) == 0


def test_thin_patches_are_reported(rota):
    assert understaffed(rota, date(2024, 3, 5), 2) == [(0, 360), (840, 1440)]
    assert gap_report(rota, date(2024, 3, 5), 2) == [
        "00:00-06:00 short by 1",
        "14:00-00:00 short by 2",
    ]


def test_an_empty_rota_loads_to_nothing():
    assert load(["", "# nobody yet"]) == []
