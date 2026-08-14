"""Text statistics."""

import re

STOP_WORDS = {"the", "a", "an", "and", "or", "of", "to", "in"}


def tokenize(text):
    """Split text into lowercase word tokens."""
    return re.findall(r"[a-z0-9']+", text.lower())


def word_count(text):
    return len(tokenize(text))


def unique_words(text, ignore_stop_words=True):
    """Set of distinct words, optionally excluding stop words."""
    words = set(tokenize(text))
    if ignore_stop_words:
        words = {w for w in words if w in STOP_WORDS}
    return words


def most_common(text, n=3):
    counts = {}
    for word in tokenize(text):
        if word not in STOP_WORDS:
            counts[word] = counts.get(word, 0) + 1
    return sorted(counts, key=lambda w: (-counts[w], w))[:n]
