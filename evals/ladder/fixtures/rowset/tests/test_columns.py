import pytest

from sheets.coerce import coerce, is_comparable, to_bool, to_int
from sheets.columns import Column, ColumnSet
from sheets.errors import ColumnError, TableError
from sheets.summary import count_by, describe, group_by, largest, mean, smallest, total

ROWS = [
    {"owner": "ana", "score": 30},
    {"owner": "bo", "score": 10},
    {"owner": "ana", "score": None},
]


def test_column_declaration():
    column = Column(" Score ", "int", required=True)
    assert column.name == "score"
    assert column.orderable
    with pytest.raises(ColumnError):
        Column("score", "date")
    with pytest.raises(ColumnError):
        Column("", "int")


def test_required_columns_reject_blanks():
    column = Column("title", "text", required=True)
    with pytest.raises(ColumnError):
        column.cast(None)


def test_boolean_columns_are_not_orderable():
    assert not Column("urgent", "bool").orderable
    assert is_comparable("float")


def test_integer_coercion_is_strict():
    assert to_int("score", "12") == 12
    assert to_int("score", 12.0) == 12
    with pytest.raises(TableError):
        to_int("score", 12.5)
    with pytest.raises(TableError):
        to_int("score", True)


def test_boolean_words():
    assert to_bool("urgent", "Yes") is True
    assert to_bool("urgent", "off") is False
    with pytest.raises(TableError):
        to_bool("urgent", "maybe")


def test_none_passes_through_every_kind():
    assert coerce("any", None, "int") is None
    assert coerce("any", None, "text") is None


def test_column_set_casts_whole_rows():
    columns = ColumnSet([Column("title", "text"), Column("score", "int")])
    assert columns.cast_row({"title": "Fix the gate"}) == {
        "title": "Fix the gate",
        "score": None,
    }
    assert columns.cast_changes({"score": "7"}) == {"score": 7}
    with pytest.raises(ColumnError):
        columns.cast_row({"nope": 1})


def test_column_set_refuses_duplicates():
    with pytest.raises(ColumnError):
        ColumnSet([Column("title"), Column("title")])


def test_summaries_ignore_empty_cells():
    assert total(ROWS, "score") == 40
    assert mean(ROWS, "score") == 20
    assert smallest(ROWS, "score") == 10
    assert largest(ROWS, "score") == 30
    assert describe(ROWS, "score") == {"count": 2, "min": 10, "max": 30, "mean": 20}


def test_grouping_counts_every_row():
    assert count_by(ROWS, "owner") == {"ana": 2, "bo": 1}
    assert [row["score"] for row in group_by(ROWS, "owner")["ana"]] == [30, None]
