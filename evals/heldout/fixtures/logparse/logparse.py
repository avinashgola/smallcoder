"""Pipe-delimited application log parsing."""

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def parse_line(line):
    """Parse a 'LEVEL|timestamp|message' log line into a dict."""
    parts = line.strip().split("|")
    if len(parts) < 3:
        raise ValueError(f"malformed log line: {line!r}")
    level, timestamp, message = parts[0], parts[1], parts[2]
    if level not in LEVELS:
        raise ValueError(f"unknown level: {level!r}")
    return {"level": level, "timestamp": timestamp, "message": message}


def parse_log(text):
    return [parse_line(line) for line in text.splitlines() if line.strip()]


def count_errors(records):
    return sum(1 for r in records if r["level"] in ("ERROR", "CRITICAL"))
