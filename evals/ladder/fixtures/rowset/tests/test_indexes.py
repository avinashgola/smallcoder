import pytest

from sheets import Column, Table
from sheets.errors import ColumnError, IndexError_
from sheets.indexes import IndexSet, LookupIndex, SortedIndex


def build_table():
    table = Table("tickets", [Column("title", "text"), Column("score", "int")])
    table.add_rows(
        [
            {"title": "Bleed the radiators", "score": 30},
            {"title": "Fix the gate", "score": 10},
            {"title": "Sand the deck", "score": 20},
            {"title": "Paint the shed", "score": 30},
        ]
    )
    return table


def test_lookup_index_buckets_rows_by_value():
    index = LookupIndex("owner")
    index.add(1, {"owner": "ana"})
    index.add(2, {"owner": "bo"})
    index.add(3, {"owner": "ana"})
    assert index.ids_for("ana") == [1, 3]
    assert index.ids_for_any(["ana", "bo"]) == [1, 2, 3]
    assert index.cardinality() == 2


def test_lookup_index_files_empty_cells():
    index = LookupIndex("owner")
    index.add(1, {"owner": None})
    assert index.ids_for(None) == [1]
    assert index.values() == [None]


def test_sorted_index_keeps_keys_in_order():
    index = SortedIndex("score")
    for row_id, score in [(1, 30), (2, 10), (3, 20), (4, 30)]:
        index.add(row_id, {"score": score})
    assert index.keys() == [10, 20, 30]
    assert index.span() == (10, 30)
    assert index.ids_for(30) == [1, 4]


def test_sorted_index_skips_empty_cells():
    index = SortedIndex("score")
    index.add(1, {"score": None})
    assert index.keys() == []
    assert len(index) == 0


def test_sorted_index_open_ended_ranges():
    index = SortedIndex("score")
    for row_id, score in [(1, 30), (2, 10), (3, 20)]:
        index.add(row_id, {"score": score})
    assert index.at_least(20) == [3, 1]
    assert index.at_most(20) == [2, 3]
    assert index.at_most(5) == []


def test_removing_the_last_row_drops_the_key():
    index = SortedIndex("score")
    index.add(1, {"score": 10})
    index.add(2, {"score": 10})
    index.remove(1, {"score": 10})
    assert index.keys() == [10]
    index.remove(2, {"score": 10})
    assert index.keys() == []
    assert 10 not in index


def test_index_set_refuses_a_second_index_on_one_column():
    indexes = IndexSet()
    indexes.add("score", ordered=True)
    with pytest.raises(IndexError_):
        indexes.add("score")
    with pytest.raises(ColumnError):
        indexes.get("owner")


def test_index_set_replace_refiles_a_row():
    indexes = IndexSet()
    indexes.add("score", ordered=True)
    indexes.insert(1, {"score": 10})
    indexes.replace(1, {"score": 10}, {"score": 20})
    assert indexes.get("score").ids_for(10) == []
    assert indexes.get("score").ids_for(20) == [1]


def test_table_keeps_its_indexes_current():
    table = build_table()
    table.add_index("score", ordered=True)
    table.update_row(2, {"score": 40})
    table.delete_row(1)
    index = table.ordered_index("score")
    assert index.keys() == [20, 30, 40]
    before = table.index_summary()
    table.rebuild_indexes()
    assert table.index_summary() == before


def test_ordered_indexes_are_refused_on_booleans():
    table = Table("flags", [Column("urgent", "bool")])
    with pytest.raises(ColumnError):
        table.add_index("urgent", ordered=True)
    assert table.ordered_index("urgent") is None
