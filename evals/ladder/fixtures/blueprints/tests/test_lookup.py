import pytest

from blueprint import Blueprint, Field
from cabinet import Cabinet
from lookup import (
    Blank,
    Both,
    Either,
    Holds,
    IsKind,
    Unless,
    ValueIs,
    ValueOver,
    WordIn,
    find,
    find_ids,
    find_one,
    newest_first,
    ordered_by,
    tally,
)


def build_cabinet():
    cabinet = Cabinet()
    cabinet.define(
        Blueprint(
            "task",
            [
                Field("title", "text", required=True),
                Field("minutes", "number"),
                Field("tags", "list"),
                Field("done", "flag"),
            ],
        )
    )
    cabinet.define(Blueprint("note", [Field("body", "text")]))
    cabinet.create("task", {"title": "Bleed the radiators", "minutes": 45, "tags": ["home"]})
    cabinet.create("task", {"title": "Fix the gate", "minutes": 0, "tags": ["home", "outdoor"]})
    cabinet.create("task", {"title": "File the receipts", "done": True})
    cabinet.create("note", {"body": "Radiator key is in the drawer"})
    return cabinet


def test_kind_and_value_terms():
    cabinet = build_cabinet()
    assert len(find(cabinet, IsKind("task"))) == 3
    assert find_ids(cabinet, ValueIs("minutes", 0)) == ["task-0002", "task-0003"]
    assert find_ids(cabinet, ValueIs("done", True)) == ["task-0003"]


def test_flags_are_not_numbers():
    cabinet = build_cabinet()
    assert find(cabinet, ValueIs("minutes", False)) == []
    assert find(cabinet, ValueIs("done", 1)) == []


def test_container_and_text_terms():
    cabinet = build_cabinet()
    assert find_ids(cabinet, Holds("tags", "home")) == ["task-0001", "task-0002"]
    assert find_ids(cabinet, WordIn("title", "RADIATOR")) == ["task-0001"]
    assert find_ids(cabinet, WordIn("body", "radiator")) == ["note-0001"]


def test_blank_covers_empty_and_absent():
    cabinet = build_cabinet()
    assert find_ids(cabinet, Blank("tags")) == ["task-0003", "note-0001"]
    assert find_ids(cabinet, Blank("body"), kind="task") == [
        "task-0001",
        "task-0002",
        "task-0003",
    ]


def test_groups():
    cabinet = build_cabinet()
    both = Both([IsKind("task"), ValueOver("minutes", 10)])
    assert find_ids(cabinet, both) == ["task-0001"]
    either = Either([Holds("tags", "outdoor"), ValueIs("done", True)])
    assert find_ids(cabinet, either) == ["task-0002", "task-0003"]
    assert find_ids(cabinet, Unless(IsKind("task"))) == ["note-0001"]


def test_helpers():
    cabinet = build_cabinet()
    assert find_one(cabinet, IsKind("note"))["body"].startswith("Radiator")
    assert find_one(cabinet, IsKind("letter")) is None
    assert tally(cabinet, "done", kind="task") == {False: 2, True: 1}
    with pytest.raises(TypeError):
        find(cabinet, "task")


def test_ordering():
    cabinet = build_cabinet()
    rows = cabinet.rows("task")
    assert [row["id"] for row in ordered_by(rows, "minutes")] == [
        "task-0002",
        "task-0003",
        "task-0001",
    ]
    assert [row["id"] for row in ordered_by(rows, "title", descending=True)][0] == "task-0002"
    assert [row["id"] for row in newest_first(cabinet.rows())][0] == "task-0003"
