"""The set of tags on one entry."""

from ..errors import TagError

MAX_TAG_LENGTH = 32


def normalize_tag(tag):
    """Return the canonical spelling of one tag."""
    if not isinstance(tag, str):
        raise TagError("tags must be strings, got %r" % (tag,))
    cleaned = tag.strip().lower()
    if not cleaned:
        raise TagError("tags must not be blank")
    if len(cleaned) > MAX_TAG_LENGTH:
        raise TagError("tag %r is too long" % (tag,))
    if any(character.isspace() for character in cleaned):
        raise TagError("tags may not contain spaces: %r" % (tag,))
    return cleaned


class TagSet:
    """A sorted, duplicate-free collection of tags."""

    def __init__(self, tags=()):
        self._tags = set()
        for tag in tags:
            self._tags.add(normalize_tag(tag))

    def add(self, tag):
        self._tags.add(normalize_tag(tag))
        return self

    def discard(self, tag):
        self._tags.discard(normalize_tag(tag))
        return self

    def holds(self, tag):
        return normalize_tag(tag) in self._tags

    def holds_all(self, tags):
        return all(self.holds(tag) for tag in tags)

    def holds_any(self, tags):
        return any(self.holds(tag) for tag in tags)

    def as_list(self):
        """The tags in sorted order - the canonical rendering."""
        return sorted(self._tags)

    def copy(self):
        return TagSet(self._tags)

    def __iter__(self):
        return iter(self.as_list())

    def __len__(self):
        return len(self._tags)

    def __contains__(self, tag):
        return tag in self._tags

    def __eq__(self, other):
        if isinstance(other, TagSet):
            return self._tags == other._tags
        if isinstance(other, (list, tuple, set)):
            return self._tags == {normalize_tag(tag) for tag in other}
        return NotImplemented

    def __repr__(self):
        return "TagSet(%r)" % (self.as_list(),)
