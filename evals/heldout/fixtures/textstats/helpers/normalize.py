"""Whitespace normalization (not involved in statistics)."""


def collapse_whitespace(text):
    return " ".join(text.split())


def strip_control_characters(text):
    return "".join(ch for ch in text if ch == "\n" or ch >= " ")
