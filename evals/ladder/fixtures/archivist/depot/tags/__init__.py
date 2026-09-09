"""Tags: a normalised set of short labels attached to an entry.

Tags are lower-cased and stripped on the way in, so ``"Home"`` and
``" home "`` are the same tag.  :class:`~depot.tags.tagset.TagSet` keeps
them sorted, which is what makes an archive of a depot byte-identical
from one run to the next.
"""

from .tagindex import TagIndex
from .tagset import TagSet, normalize_tag

__all__ = ["TagSet", "TagIndex", "normalize_tag"]
