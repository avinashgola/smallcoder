"""Finding records in a cabinet.

Terms describe what to keep, :mod:`lookup.run` applies them and
:mod:`lookup.sortkeys` orders what comes back.

    from lookup import Holds, IsKind, find

    find(cabinet, Holds("tags", "home"))
"""

from .run import find, find_ids, find_one, tally
from .sortkeys import newest_first, ordered_by
from .terms import (
    Both,
    Blank,
    Either,
    Holds,
    IsKind,
    Term,
    Unless,
    ValueIs,
    ValueOver,
    WordIn,
)

__all__ = [
    "Term",
    "IsKind",
    "ValueIs",
    "ValueOver",
    "Holds",
    "WordIn",
    "Blank",
    "Both",
    "Either",
    "Unless",
    "find",
    "find_ids",
    "find_one",
    "tally",
    "ordered_by",
    "newest_first",
]
