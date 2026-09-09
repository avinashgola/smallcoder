"""Saving a cabinet to plain data and loading it back.

A saved cabinet carries its blueprints as well as its records, so a
reloaded cabinet builds new records the same way the original did.

    text = dumps(cabinet)
    restored = loads(text)
"""

from .read import load, loads, read_registry
from .write import FORMAT_VERSION, dump, dumps, summary

__all__ = ["dump", "dumps", "load", "loads", "read_registry", "summary", "FORMAT_VERSION"]
