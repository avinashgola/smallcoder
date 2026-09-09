from layout.banner import box, inner_width, titled_box
from layout.bullets import bullet_list, numbered_list
from layout.indent import common_prefix, dedent, hanging_indent, indent
from layout.paragraphs import count_words, format_document, split_paragraphs


def test_split_paragraphs_joins_wrapped_source_lines():
    text = "first line\nsecond line\n\n   third\n"
    assert split_paragraphs(text) == ["first line second line", "third"]


def test_count_words():
    assert count_words("one two\n\nthree") == 3


def test_format_document_separates_paragraphs():
    text = "alpha beta\n\ngamma"
    assert format_document(text, 20) == "alpha beta\n\ngamma"
    assert format_document(text, 20, gap=2) == "alpha beta\n\n\ngamma"


def test_indent_skips_blank_lines():
    assert indent(["a", "", "b"], "..") == ["..a", "", "..b"]


def test_hanging_indent():
    assert hanging_indent(["a", "b"], "* ", "  ") == ["* a", "  b"]


def test_common_prefix_and_dedent():
    lines = ["    a", "", "      b"]
    assert common_prefix(lines) == "    "
    assert dedent(lines) == ["a", "", "  b"]


def test_bullet_list_aligns_continuations():
    assert bullet_list(["alpha beta gamma delta"], 14) == [
        "- alpha beta",
        "  gamma delta",
    ]


def test_numbered_list():
    assert numbered_list(["one two", "three"], 20) == ["1. one two", "2. three"]


def test_inner_width():
    assert inner_width(20) == 16


def test_box_is_exactly_the_requested_width():
    lines = box("hello world", 20)
    assert all(len(line) == 20 for line in lines)
    assert lines[0] == "+" + "-" * 18 + "+"
    assert lines[1] == "| hello world      |"


def test_titled_box_centres_the_heading():
    lines = titled_box("notes", "hello world", 20)
    assert len(lines) == 5
    assert lines[1].strip("|").strip() == "NOTES"
    assert all(len(line) == 20 for line in lines)
