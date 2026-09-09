from tabular.columns import column_widths, detect_alignments, fit_widths, normalize_rows
from tabular.markdown import divider_cell, markdown_table, markdown_text
from tabular.table import render_row, render_table, render_text

HEADERS = ["name", "qty"]
ROWS = [["apple", 3], ["fig", 12]]


def test_normalize_rows_squares_the_grid():
    assert normalize_rows([["a"], ["b", 2]]) == [["a", ""], ["b", "2"]]
    assert normalize_rows([["a", "b", "c"]], 2) == [["a", "b"]]


def test_column_widths():
    rows = normalize_rows([HEADERS] + ROWS)
    assert column_widths(rows) == [5, 3]
    assert column_widths(rows, maximum=4) == [4, 3]


def test_fit_widths_shaves_the_widest_column():
    assert fit_widths([5, 3, 2], 8) == [3, 3, 2]
    assert fit_widths([2, 2], 10) == [2, 2]
    assert fit_widths([1, 1], 1) == [1, 1]


def test_detect_alignments_per_column():
    assert detect_alignments(normalize_rows(ROWS)) == ["left", "right"]


def test_render_row():
    assert render_row(["a", "12"], [3, 4], ["left", "right"]) == "| a   |   12 |"


def test_render_table():
    assert render_table(HEADERS, ROWS) == [
        "+-------+-----+",
        "| name  | qty |",
        "+-------+-----+",
        "| apple |   3 |",
        "| fig   |  12 |",
        "+-------+-----+",
    ]


def test_every_rendered_line_has_the_same_width():
    lines = render_table(["heading", "n"], [["x", 1], ["longer value", 22]])
    assert len(set(len(line) for line in lines)) == 1


def test_render_table_respects_a_total_width():
    lines = render_table(HEADERS, ROWS, total=6)
    assert lines[0] == "+-----+-----+"


def test_render_text_joins_the_lines():
    assert render_text(HEADERS, ROWS).splitlines() == render_table(HEADERS, ROWS)


def test_divider_cell():
    assert divider_cell(5, "left") == "-----"
    assert divider_cell(5, "right") == "----:"
    assert divider_cell(5, "center") == ":---:"


def test_markdown_table():
    assert markdown_table(["item", "cost"], [["tea", 2], ["coffee", 10]]) == [
        "|  item  | cost |",
        "| ------ | ---: |",
        "| tea    |    2 |",
        "| coffee |   10 |",
    ]


def test_markdown_text_joins_the_lines():
    table = markdown_table(HEADERS, ROWS)
    assert markdown_text(HEADERS, ROWS) == "\n".join(table)
