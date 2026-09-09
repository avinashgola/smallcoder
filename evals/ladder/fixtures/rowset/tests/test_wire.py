import pytest

from sheets import Column, Table
from sheets.errors import TableError
from wire import dump_table, load_table
from wire.header import format_header, parse_column, parse_header
from wire.text import format_cell


def build_table():
    table = Table(
        "tickets",
        [
            Column("title", "text", required=True),
            Column("score", "int"),
            Column("urgent", "bool"),
        ],
    )
    table.add_rows(
        [
            {"title": "Bleed the radiators", "score": 30, "urgent": False},
            {"title": "Fix the gate", "urgent": True},
        ]
    )
    return table


def test_round_trip_keeps_rows_and_ids():
    table = build_table()
    restored = load_table(dump_table(table))
    assert restored.items() == table.items()
    assert restored.name == table.name


def test_round_trip_keeps_the_column_declarations():
    table = build_table()
    restored = load_table(dump_table(table))
    assert restored.columns.kinds() == table.columns.kinds()
    with pytest.raises(TableError):
        restored.add_row({"score": 1})


def test_reloaded_tables_keep_handing_out_fresh_ids():
    table = build_table()
    restored = load_table(dump_table(table))
    assert restored.add_row({"title": "Sand the deck"}) == 3


def test_tabs_and_newlines_survive():
    table = Table("notes", [Column("body", "text")])
    table.add_row({"body": "first\tsecond\nthird"})
    restored = load_table(dump_table(table))
    assert restored.row(1)["body"] == "first\tsecond\nthird"


def test_the_empty_marker_is_escaped():
    table = Table("notes", [Column("body", "text")])
    table.add_rows([{"body": "~"}, {}])
    restored = load_table(dump_table(table))
    assert restored.row(1)["body"] == "~"
    assert restored.row(2)["body"] is None
    assert format_cell(None) == "~"


def test_header_describes_the_columns():
    lines = format_header(build_table())
    assert lines[0] == "# rowset 1 tickets"
    assert lines[1] == "#! id\ttitle:text!\tscore:int\turgent:bool"
    name, columns = parse_header(lines)
    assert name == "tickets"
    assert [column.name for column in columns] == ["title", "score", "urgent"]
    assert columns[0].required


def test_broken_dumps_are_refused():
    with pytest.raises(TableError):
        load_table("# something else 1 tickets\n#! id\ttitle:text\n")
    with pytest.raises(TableError):
        parse_column("score")
    with pytest.raises(TableError):
        load_table("# rowset 1 tickets\n#! id\ttitle:text\n1\ttoo\tmany\n")
