"""Which entries carry which tag."""


class TagIndex:
    """A tag -> entry ids index, kept in step with the depot."""

    def __init__(self):
        self._by_tag = {}

    def add(self, entry_id, tags):
        for tag in tags:
            self._by_tag.setdefault(tag, set()).add(entry_id)

    def remove(self, entry_id, tags):
        for tag in tags:
            holders = self._by_tag.get(tag)
            if holders is None:
                continue
            holders.discard(entry_id)
            if not holders:
                del self._by_tag[tag]

    def replace(self, entry_id, previous, updated):
        """Refile ``entry_id`` after its tags changed."""
        self.remove(entry_id, previous)
        self.add(entry_id, updated)

    def ids_for(self, tag):
        return sorted(self._by_tag.get(tag, ()))

    def ids_for_all(self, tags):
        """Ids carrying every one of ``tags``."""
        found = None
        for tag in tags:
            holders = set(self._by_tag.get(tag, ()))
            found = holders if found is None else found & holders
        return sorted(found or ())

    def ids_for_any(self, tags):
        found = set()
        for tag in tags:
            found.update(self._by_tag.get(tag, ()))
        return sorted(found)

    def tags(self):
        return sorted(self._by_tag)

    def counts(self):
        return {tag: len(holders) for tag, holders in self._by_tag.items()}

    def rebuild(self, entries):
        self._by_tag = {}
        for entry in entries:
            self.add(entry.id, entry.tags)

    def clear(self):
        self._by_tag = {}

    def __len__(self):
        return len(self._by_tag)
