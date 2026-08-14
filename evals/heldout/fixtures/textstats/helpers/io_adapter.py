"""Document loading helpers (not involved in statistics)."""

from pathlib import Path


def load_document(path):
    return Path(path).read_text(encoding="utf-8")


def load_directory(directory):
    return {p.name: load_document(p) for p in sorted(Path(directory).glob("*.txt"))}
