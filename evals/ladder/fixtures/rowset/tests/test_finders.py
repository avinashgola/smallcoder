import pytest

from finders import (
    AnyOf,
    AtLeast,
    AtMost,
    Equals,
    EveryOf,
    InRange,
    Matches,
    Negate,
    OneOf,
    select,
)
from finders.planner import plan
from finders.scan import scan_rows
from sheets import Column, Table
from sheets.errors import TableError

ROWS = [
    {"title": "Bleed the radiators", "score": 30, "owner": "ana"},
    {"title": "Fix the gate", "score": 10, "owner": "bo"},
    {"title": "Sand the deck", "score": 20, "owner": "ana"},
    {"title": "Paint the shed", "score": 30, "owner": None},
    {"title": "Oil the hinges", "score": None, "owner": "bo"},
]


def build_table(indexed=True):
    table = Table(
        "tickets",
        [Column("title", "text"), Column("score", "int"), Column("owner", "text")],
    )
    table.add_rows(ROWS)
    if indexed:
        table.add_index("score", ordered=True)
        table.add_index("owner")
    return table


def titles(result):
    return [row["title"] for row in result.rows()]


def test_equality_uses_an_index_when_there_is_one():
    table = build_table()
    assert titles(select(table, Equals("owner", "ana"))) == [
        "Bleed the radiators",
        "Sand the deck",
    ]
    assert plan(table, Equals("owner", "ana"))["strategy"] == "index"
    assert plan(table, Equals("title", "Fix the gate"))["strategy"] == "scan"


def test_range_includes_both_bounds():
    table = build_table()
    assert titles(select(table, InRange("score", 10, 20))) == [
        "Fix the gate",
        "Sand the deck",
    ]
    assert titles(select(table, InRange("score", 20, 30))) == [
        "Bleed the radiators",
        "Sand the deck",
        "Paint the shed",
    ]


def test_an_index_answers_a_range_the_same_way_a_scan_does():
    indexed = build_table(indexed=True)
    plain = build_table(indexed=False)
    condition = InRange("score", 10, 30)
    assert titles(select(indexed, condition)) == titles(select(plain, condition))
    assert titles(select(indexed, condition)) == [
        "Bleed the radiators",
        "Fix the gate",
        "Sand the deck",
        "Paint the shed",
    ]


def test_a_single_point_range_finds_its_rows():
    table = build_table()
    assert titles(select(table, InRange("score", 30, 30))) == [
        "Bleed the radiators",
        "Paint the shed",
    ]


def test_open_ended_comparisons():
    table = build_table()
    assert titles(select(table, AtMost("score", 20))) == ["Fix the gate", "Sand the deck"]
    assert titles(select(table, AtLeast("score", 30))) == [
        "Bleed the radiators",
        "Paint the shed",
    ]


def test_empty_cells_never_fall_in_a_range():
    table = build_table()
    assert "Oil the hinges" not in titles(select(table, InRange("score", 0, 100)))
    assert titles(select(table, Equals("score", None))) == ["Oil the hinges"]


def test_membership_and_negation():
    table = build_table()
    assert titles(select(table, OneOf("owner", ["bo"]))) == ["Fix the gate", "Oil the hinges"]
    assert titles(select(table, Negate(Equals("owner", "ana")))) == [
        "Fix the gate",
        "Paint the shed",
        "Oil the hinges",
    ]


def test_groups_narrow_and_widen():
    table = build_table()
    both = EveryOf([InRange("score", 20, 30), Equals("owner", "ana")])
    assert titles(select(table, both)) == ["Bleed the radiators", "Sand the deck"]
    either = AnyOf([Equals("owner", "bo"), InRange("score", 30, 30)])
    assert titles(select(table, either)) == [
        "Bleed the radiators",
        "Fix the gate",
        "Paint the shed",
        "Oil the hinges",
    ]


def test_text_search_falls_back_to_a_scan():
    table = build_table()
    assert titles(select(table, Matches("title", "THE GATE"))) == ["Fix the gate"]
    assert plan(table, Matches("title", "gate"))["strategy"] == "scan"


def test_results_can_be_ordered_and_trimmed():
    table = build_table()
    result = select(table, AtLeast("score", 10), order="score", descending=True)
    assert titles(result.limit(2)) == ["Bleed the radiators", "Paint the shed"]
    assert result.first()["score"] == 30
    assert titles(select(table, Equals("owner", "nobody"))) == []
    assert select(table, Equals("owner", "nobody")).is_empty()


def test_a_scan_is_the_reference_for_every_condition():
    table = build_table()
    for condition in [
        Equals("owner", "ana"),
        OneOf("owner", ["ana", "bo"]),
        InRange("score", 10, 30),
        AtLeast("score", 20),
        AtMost("score", 20),
        EveryOf([InRange("score", 20, 30), Equals("owner", "ana")]),
    ]:
        expected = [row["title"] for row in scan_rows(table, condition)]
        assert titles(select(table, condition)) == expected


def test_inside_out_ranges_are_refused():
    with pytest.raises(TableError):
        InRange("score", 30, 10)
