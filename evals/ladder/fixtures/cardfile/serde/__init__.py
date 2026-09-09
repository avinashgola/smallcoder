"""Snapshotting a catalogue to JSON-friendly data and back again.

``dump``/``load`` work on plain Python structures; ``dumps``/``loads``
add the JSON text layer.  A snapshot carries the records, their ids and
the index definitions, so a restored store answers lookups the same way
the original did.
"""

from .decode import load, loads, restore_indexes
from .encode import dump, dumps, snapshot_summary
from .values import decode_value, encode_value

__all__ = [
    "dump",
    "dumps",
    "load",
    "loads",
    "restore_indexes",
    "snapshot_summary",
    "encode_value",
    "decode_value",
]
