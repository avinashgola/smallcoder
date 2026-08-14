from textstats import most_common, tokenize, unique_words, word_count

TEXT = "The quick brown fox jumps over the lazy dog and the quick fox naps"


def test_tokenize():
    assert tokenize("Hello, World!") == ["hello", "world"]


def test_word_count():
    assert word_count(TEXT) == 14


def test_unique_words_excludes_stop_words():
    words = unique_words(TEXT)
    assert "quick" in words
    assert "fox" in words
    assert "the" not in words
    assert "and" not in words


def test_unique_words_can_include_stop_words():
    words = unique_words(TEXT, ignore_stop_words=False)
    assert "the" in words
    assert "quick" in words


def test_unique_words_are_distinct():
    assert len(unique_words("dog dog dog")) == 1


def test_most_common():
    assert most_common(TEXT, n=2) == ["fox", "quick"]
