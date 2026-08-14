import pytest

from logparse import count_errors, parse_line, parse_log

LOG = """INFO|2024-01-01T10:00:00|service started
ERROR|2024-01-01T10:00:05|db failure: timeout|retry=3
WARNING|2024-01-01T10:00:09|disk usage high
"""


def test_simple_line():
    record = parse_line("INFO|2024-01-01T10:00:00|service started")
    assert record["level"] == "INFO"
    assert record["timestamp"] == "2024-01-01T10:00:00"
    assert record["message"] == "service started"


def test_message_containing_pipes_is_preserved():
    record = parse_line("ERROR|2024-01-01T10:00:05|db failure: timeout|retry=3")
    assert record["message"] == "db failure: timeout|retry=3"


def test_message_with_several_pipes():
    record = parse_line("DEBUG|t0|a|b|c")
    assert record["message"] == "a|b|c"


def test_parse_log_counts():
    records = parse_log(LOG)
    assert len(records) == 3
    assert count_errors(records) == 1


def test_malformed_line_rejected():
    with pytest.raises(ValueError):
        parse_line("INFO|only-two-fields")


def test_unknown_level_rejected():
    with pytest.raises(ValueError):
        parse_line("TRACE|t0|message")
