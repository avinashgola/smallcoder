from diffcore.sequence import diff_lines
from render.inline import changed_line_numbers, inline_lines, side_by_side, summarize
from render.unified import hunk_header, unified_diff, unified_text


def test_unified_diff_of_a_replacement():
    assert unified_diff(["a", "b", "c"], ["a", "x", "c"]) == [
        "@@ -1,3 +1,3 @@",
        " a",
        "-b",
        "+x",
        " c",
    ]


def test_unified_diff_of_a_pure_insertion():
    assert unified_diff(["a", "b"], ["a", "new", "b"]) == [
        "@@ -1,2 +1,3 @@",
        " a",
        "+new",
        " b",
    ]


def test_unified_diff_of_a_pure_deletion():
    assert unified_diff(["a", "b", "c"], ["a", "c"]) == [
        "@@ -1,3 +1,2 @@",
        " a",
        "-b",
        " c",
    ]


def test_unified_diff_of_identical_input_is_empty():
    assert unified_diff(["a", "b"], ["a", "b"]) == []


def test_unified_diff_emits_one_header_per_hunk():
    old = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    new = ["a", "B", "c", "d", "e", "f", "g", "h", "I", "j"]
    lines = unified_diff(old, new, context=1)
    assert [line for line in lines if line.startswith("@@")] == [
        "@@ -1,3 +1,3 @@",
        "@@ -8,3 +8,3 @@",
    ]


def test_hunk_header_of_an_appended_block():
    ops = diff_lines(["a"], ["a", "b", "c"])
    assert hunk_header(ops) == "@@ -1,1 +1,3 @@"


def test_unified_text_joins_lines():
    assert unified_text("a\nb\n", "a\nx\n") == "@@ -1,2 +1,2 @@\n a\n-b\n+x"


def test_unified_text_of_an_appended_line():
    assert unified_text("a\n", "a\nb\n") == "@@ -1,1 +1,2 @@\n a\n+b"


def test_summarize():
    assert summarize(diff_lines(["a"], ["a"])) == "no changes"
    assert summarize(diff_lines(["a", "b"], ["a", "x"])) == "1 added, 1 removed"


def test_summarize_counts_an_insertion_as_a_change():
    assert summarize(diff_lines(["a"], ["a", "b"])) == "1 added, 0 removed"


def test_inline_lines_mark_every_side():
    ops = diff_lines(["a", "b"], ["a", "x"])
    assert inline_lines(ops) == ["  a", "- b", "+ x"]


def test_side_by_side_puts_each_change_in_one_column():
    ops = diff_lines(["a", "b"], ["a", "x"])
    rows = side_by_side(ops, 4)
    columns = [tuple(part.strip() for part in row.split("|")) for row in rows]
    assert columns == [("a", "a"), ("b", ""), ("", "x")]


def test_changed_line_numbers_are_one_based():
    removed, added = changed_line_numbers(diff_lines(["a", "b", "c"], ["a", "x", "c"]))
    assert removed == [2]
    assert added == [2]
