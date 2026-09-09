import pytest

from sheets import Column, RowNotFound, Table
from sheets.errors import ColumnError, TableError
from sheets.table import table_from_spec


def build_table():
    table = Table(
        "tickets",
        [
            Column("title", "text", required=True),
            Column("score", "int"),
            Column("owner", "text"),
            Column("urgent", "bool"),
        ],
    )
    table.add_rows(
        [
            {"title": "Bleed the radiators", "score": 30, "owner": "ana"},
            {"title": "Fix the gate", "score": 10, "owner": "bo", "urgent": True},
            {"title": "Sand the deck", "score": 20},
        ]
    )
    return table


def test_rows_have_every_column():
    table = build_table()
    assert table.row(3) == {
        "title": "Sand the deck",
        "score": 20,
        "owner": None,
        "urgent": None,
    }


def test_ids_are_handed_out_in_order():
    table = build_table()
    assert table.ids() == [1, 2, 3]
    assert len(table) == 3
    assert 2 in table


def test_rows_handed_out_are_copies():
    table = build_table()
    borrowed = table.row(1)
    borrowed["title"] = "changed"
    assert table.row(1)["title"] == "Bleed the radiators"


def test_values_are_coerced_to_the_declared_type():
    table = build_table()
    row_id = table.add_row({"title": "  Oil the hinges ", "score": "40", "urgent": "yes"})
    row = table.row(row_id)
    assert row["title"] == "Oil the hinges"
    assert row["score"] == 40
    assert row["urgent"] is True


def test_bad_values_are_refused():
    table = build_table()
    with pytest.raises(TableError):
        table.add_row({"title": "Broken", "score": "quite high"})
    with pytest.raises(ColumnError):
        table.add_row({"title": "Broken", "colour": "red"})
    with pytest.raises(ColumnError):
        table.add_row({"score": 1})


def test_update_writes_only_the_named_columns():
    table = build_table()
    updated = table.update_row(2, {"score": 15})
    assert updated["score"] == 15
    assert updated["title"] == "Fix the gate"
    with pytest.raises(ColumnError):
        table.update_row(2, {})


def test_delete_forgets_the_row():
    table = build_table()
    table.delete_row(2)
    assert table.ids() == [1, 3]
    with pytest.raises(RowNotFound):
        table.row(2)
    assert table.peek(2, default="gone") == "gone"


def test_deleted_ids_are_not_reused():
    table = build_table()
    table.delete_row(3)
    assert table.add_row({"title": "Oil the hinges"}) == 4


def test_restore_row_keeps_ids_unique():
    table = build_table()
    table.restore_row(9, {"title": "Imported"})
    assert table.add_row({"title": "Next"}) == 10
    with pytest.raises(TableError):
        table.restore_row(9, {"title": "Again"})


def test_column_helpers():
    table = build_table()
    assert table.column_values("owner") == ["ana", "bo", None]
    assert table.distinct("owner") == ["ana", "bo", None]
    assert table.column_names() == ["title", "score", "owner", "urgent"]
    with pytest.raises(ColumnError):
        table.column_values("colour")


def test_table_from_spec():
    table = table_from_spec("notes", {"body": "text", "pinned": "bool"})
    assert table.column_names() == ["body", "pinned"]
