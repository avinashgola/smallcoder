import pytest

from catalog.errors import QueryError
from query import Query, build_predicate, run_spec
from query.ordering import order_by, parse_order
from query.paging import describe_page, page_count, page_of

ROWS = [
    {"title": "Bleed the radiators", "status": "open", "score": 30, "owner": "ana"},
    {"title": "Fix the gate", "status": "open", "score": 10, "owner": "bo"},
    {"title": "Sand the deck", "status": "done", "score": 20, "owner": "ana"},
    {"title": "Paint the shed", "status": "open", "score": 20},
]


def titles(rows):
    return [row["title"] for row in rows]


def test_exact_match():
    assert titles(run_spec(ROWS, {"status": "done"})) == ["Sand the deck"]


def test_comparisons():
    found = run_spec(ROWS, {"score": {"$gte": 20}})
    assert titles(found) == ["Bleed the radiators", "Sand the deck", "Paint the shed"]


def test_between_includes_both_bounds():
    found = run_spec(ROWS, {"score": {"$between": [10, 20]}})
    assert titles(found) == ["Fix the gate", "Sand the deck", "Paint the shed"]


def test_membership_and_negation():
    assert titles(run_spec(ROWS, {"owner": {"$in": ["bo"]}})) == ["Fix the gate"]
    assert titles(run_spec(ROWS, {"$not": {"status": "open"}})) == ["Sand the deck"]


def test_alternatives():
    spec = {"$or": [{"owner": "bo"}, {"status": "done"}]}
    assert titles(run_spec(ROWS, spec)) == ["Fix the gate", "Sand the deck"]


def test_presence():
    assert titles(run_spec(ROWS, {"owner": {"$present": False}})) == ["Paint the shed"]


def test_contains_is_case_insensitive_by_default():
    assert titles(run_spec(ROWS, {"title": {"$contains": "GATE"}})) == ["Fix the gate"]


def test_unknown_operators_are_rejected():
    with pytest.raises(QueryError):
        build_predicate({"score": {"$approx": 10}})
    with pytest.raises(QueryError):
        build_predicate({"$magic": 1})


def test_ordering_is_stable_across_mixed_directions():
    ordered = order_by(ROWS, ["status", "-score"])
    assert titles(ordered) == [
        "Sand the deck",
        "Bleed the radiators",
        "Paint the shed",
        "Fix the gate",
    ]


def test_ordering_tolerates_missing_values():
    rows = [{"n": 2}, {}, {"n": 1}]
    assert order_by(rows, "n") == [{}, {"n": 1}, {"n": 2}]
    assert parse_order("-n") == ("n", True)


def test_query_composes():
    query = Query.from_spec({"status": "open"}).where({"score": {"$gte": 20}})
    assert titles(query.run(ROWS)) == ["Bleed the radiators", "Paint the shed"]
    assert query.count(ROWS) == 2
    assert query.first(ROWS)["title"] == "Bleed the radiators"


def test_paging():
    assert titles(run_spec(ROWS, None, limit=2)) == ["Bleed the radiators", "Fix the gate"]
    assert titles(run_spec(ROWS, None, limit=2, offset=2)) == ["Sand the deck", "Paint the shed"]
    assert page_count(4, 3) == 2
    assert titles(page_of(ROWS, 2, 3)) == ["Paint the shed"]
    assert describe_page(4, 2, 3) == (4, 4, 2)
