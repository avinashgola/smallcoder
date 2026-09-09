from wrapping.filler import fill, fill_lines, shorten, wrap
from wrapping.measure import display_width, expand_tabs, pad, truncate
from wrapping.tokens import break_long_word, normalize, prepare, split_words


def test_expand_tabs_moves_to_the_next_stop():
    assert expand_tabs("a\tb") == "a   b"
    assert expand_tabs("\tx") == "    x"
    assert expand_tabs("abcd\te") == "abcd    e"


def test_display_width_ignores_zero_width_characters():
    assert display_width("a\tb") == 5
    assert display_width("ab\u200b") == 2


def test_truncate():
    assert truncate("hi", 8) == "hi"
    assert truncate("hello world", 8) == "hello..."
    assert truncate("hello", 2) == "he"
    assert truncate("hello", 0) == ""


def test_pad_alignments():
    assert pad("ab", 6) == "ab    "
    assert pad("ab", 6, "right") == "    ab"
    assert pad("ab", 6, "center") == "  ab  "
    assert pad("abcdef", 3) == "abcdef"


def test_normalize_and_split_words():
    assert normalize("  a  b\tc ") == "a b c"
    assert split_words("  a  b\tc ") == ["a", "b", "c"]
    assert split_words("   ") == []


def test_break_long_word():
    assert break_long_word("abcdefgh", 3) == ["abc", "def", "gh"]
    assert break_long_word("well-behaved", 8) == ["well-", "behaved"]


def test_prepare_splits_only_oversized_words():
    assert prepare("short abcdefgh", 4) == ["shor", "t", "abcd", "efgh"]


def test_word_that_exactly_fills_the_line_stays_on_it():
    assert wrap("ab cd", 5) == ["ab cd"]
    assert fill_lines(["ab", "cd"], 5) == ["ab cd"]


def test_greedy_wrap_uses_the_whole_width():
    text = "the quick brown fox jumps over the lazy dog"
    assert wrap(text, 10) == [
        "the quick",
        "brown fox",
        "jumps over",
        "the lazy",
        "dog",
    ]


def test_wrap_breaks_when_a_word_does_not_fit():
    assert wrap("ab cd", 4) == ["ab", "cd"]


def test_no_line_is_wider_than_the_limit():
    text = "alpha beta gamma delta epsilon zeta eta theta"
    for width in range(6, 20):
        assert all(len(line) <= width for line in wrap(text, width))


def test_fill_joins_lines():
    assert fill("one two three", 7) == "one two\nthree"


def test_shorten_leaves_a_single_line_alone():
    assert shorten("hello there", 20) == "hello there"
