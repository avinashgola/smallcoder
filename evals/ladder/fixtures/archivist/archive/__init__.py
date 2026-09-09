"""Writing a depot out and reading it back.

An archive is JSON: a manifest with the format version, an entry count
and a digest, followed by the entries themselves.  The digest is taken
over the encoded entries, so a truncated or hand-edited archive is
rejected instead of loaded half way.

    text = dumps(depot)
    restored = loads(text)
"""

from .manifest import FORMAT_VERSION, build_manifest, check_manifest, digest_of
from .reader import decode_entry, load, loads
from .writer import dump, dumps, encode_entry

__all__ = [
    "dump",
    "dumps",
    "load",
    "loads",
    "encode_entry",
    "decode_entry",
    "build_manifest",
    "check_manifest",
    "digest_of",
    "FORMAT_VERSION",
]
