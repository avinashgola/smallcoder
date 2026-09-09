import pytest

from align.borders import join_cells, row_width, rule
from align.cells import center, clip, clip_middle, left, right
from align.rules import CENTER, LEFT, RIGHT, detect_alignment, looks_numeric, place


def test_clip():
    assert clip("hello", 8) == "hello"
    assert clip("hello world", 8) == "hello..."
    assert clip("hello", 2) == "he"
    assert clip("hello", 0) == ""


def test_clip_middle_keeps_both_ends():
    assert clip_middle("abcdefghij", 9) == "abc...hij"
    assert clip_middle("short", 9) == "short"


def test_left_and_right():
    assert left("ab", 5) == "ab   "
    assert right("ab", 5) == "   ab"
    assert left("abcdef", 3) == "abcdef"
    assert right("ab", 5, ".") == "...ab"


def test_center_splits_the_padding_evenly():
    assert center("ab", 6) == "  ab  "
    assert center("ab", 2) == "ab"
    assert center("abcdef", 3) == "abcdef"


def test_center_gives_the_odd_column_to_the_right():
    assert center("abc", 6) == " abc  "
    assert center("x", 4) == " x  "


def test_center_never_overflows_the_field():
    for width in range(1, 12):
        assert len(center("abc", width)) == max(width, 3)


def test_place_dispatches_on_the_alignment_name():
    assert place("x", 5, LEFT) == "x    "
    assert place("x", 5, RIGHT) == "    x"
    assert place("x", 5, CENTER) == "  x  "
    with pytest.raises(ValueError):
        place("x", 5, "middle")


def test_looks_numeric():
    assert looks_numeric("12")
    assert looks_numeric(" -3.5 ")
    assert looks_numeric("1,200")
    assert looks_numeric("87%")
    assert not looks_numeric("12a")
    assert not looks_numeric("1.2.3")
    assert not looks_numeric("")


def test_detect_alignment():
    assert detect_alignment(["1", "2", ""]) == RIGHT
    assert detect_alignment(["1", "two"]) == LEFT
    assert detect_alignment(["", "  "]) == LEFT


def test_rule_matches_the_column_widths():
    assert rule([3, 2]) == "+-----+----+"


def test_join_cells():
    assert join_cells(["ab ", "c"]) == "| ab  | c |"


def test_row_width_matches_what_is_printed():
    widths = [3, 2]
    assert row_width(widths) == len(rule(widths))
