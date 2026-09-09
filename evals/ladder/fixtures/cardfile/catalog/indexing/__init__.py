"""Secondary indexes for the catalogue.

An index maps a *key* derived from one field to the ids of the records
that carry it.  Two flavours exist: :class:`~catalog.indexing.hash_index.HashIndex`
for ordinary many-to-one fields and
:class:`~catalog.indexing.unique_index.UniqueIndex` for fields that must
identify at most one record.  :class:`~catalog.indexing.registry.IndexRegistry`
owns a store's indexes and is the only thing the store talks to.
"""

from .hash_index import HashIndex
from .keys import MISSING, index_key, keys_for
from .registry import IndexRegistry
from .unique_index import UniqueIndex

__all__ = [
    "HashIndex",
    "UniqueIndex",
    "IndexRegistry",
    "index_key",
    "keys_for",
    "MISSING",
]
