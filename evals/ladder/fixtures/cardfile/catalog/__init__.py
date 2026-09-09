"""cardfile - a very small in-memory record catalogue.

The library is deliberately plain: records are ordinary dictionaries, ids
are short strings and everything lives in memory.  It is split into four
parts:

``catalog``           the store itself plus the record helpers it uses
``catalog.indexing``  secondary indexes that are kept in step with the store
``query``             predicates and the little engine that runs them
``serde``             snapshot encoding and decoding

Typical use::

    store = Store()
    store.add_index("status")
    store.insert({"title": "Wire the porch light", "status": "open"})
    store.find("status", "open")
"""

from .errors import CatalogError, DuplicateKey, QueryError, RecordNotFound, SchemaError
from .store import Store

__all__ = [
    "Store",
    "CatalogError",
    "DuplicateKey",
    "QueryError",
    "RecordNotFound",
    "SchemaError",
]
