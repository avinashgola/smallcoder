"""The depot: entries in insertion order, with a tag index beside them.

Every read hands back a copy of the entry, so nothing a caller does to
what it was given can put the tag index out of step with the entries.
Every write bumps the revision of the entry it touched, which is what
lets an archive be compared against a live depot.
"""

from .counters import Counter, next_revision
from .entry import Entry, normalize_fields, normalize_name
from .errors import DepotError, EntryNotFound
from .tags.tagindex import TagIndex
from .tags.tagset import TagSet, normalize_tag


class Depot:
    """An ordered collection of tagged entries."""

    def __init__(self):
        self._entries = {}
        self._order = []
        self._counter = Counter()
        self._tags = TagIndex()

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------
    def add(self, fields=None, tags=(), entry_id=None):
        """Store a new entry and return it."""
        if entry_id is None:
            entry_id = self._counter.next_id()
        elif entry_id in self._entries:
            raise DepotError("id %r is already in use" % (entry_id,))
        else:
            self._counter.observe(entry_id)
        entry = Entry(entry_id, fields or {}, TagSet(tags))
        self._entries[entry_id] = entry
        self._order.append(entry_id)
        self._tags.add(entry_id, entry.tags)
        return entry.copy()

    def restore(self, entry):
        """Put an entry back exactly as it was, id and revision included."""
        if not isinstance(entry, Entry):
            raise DepotError("expected an Entry, got %r" % (entry,))
        if entry.id in self._entries:
            raise DepotError("id %r is already in use" % (entry.id,))
        self._counter.observe(entry.id)
        stored = entry.copy()
        self._entries[stored.id] = stored
        self._order.append(stored.id)
        self._tags.add(stored.id, stored.tags)
        return stored.copy()

    def amend(self, entry_id, changes):
        """Write ``changes`` into an entry and bump its revision."""
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFound(entry_id)
        if not changes:
            raise DepotError("an empty change set would do nothing")
        entry.fields.update(normalize_fields(changes))
        entry.revision = next_revision(entry.revision)
        return entry.copy()

    def drop_field(self, entry_id, name):
        """Remove one field from an entry, bumping its revision."""
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFound(entry_id)
        field = normalize_name(name)
        if field not in entry.fields:
            return entry.copy()
        del entry.fields[field]
        entry.revision = next_revision(entry.revision)
        return entry.copy()

    def retag(self, entry_id, tags):
        """Replace an entry's tags, bumping its revision."""
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFound(entry_id)
        previous = entry.tags
        entry.tags = TagSet(tags)
        entry.revision = next_revision(entry.revision)
        self._tags.replace(entry_id, previous, entry.tags)
        return entry.copy()

    def tag(self, entry_id, tag):
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFound(entry_id)
        return self.retag(entry_id, entry.tags.as_list() + [normalize_tag(tag)])

    def untag(self, entry_id, tag):
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFound(entry_id)
        remaining = [held for held in entry.tags if held != normalize_tag(tag)]
        return self.retag(entry_id, remaining)

    def remove(self, entry_id):
        entry = self._entries.pop(entry_id, None)
        if entry is None:
            raise EntryNotFound(entry_id)
        self._order.remove(entry_id)
        self._tags.remove(entry_id, entry.tags)
        return entry

    def clear(self):
        self._entries = {}
        self._order = []
        self._tags.clear()

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------
    def get(self, entry_id):
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFound(entry_id)
        return entry.copy()

    def peek(self, entry_id, default=None):
        entry = self._entries.get(entry_id)
        return default if entry is None else entry.copy()

    def ids(self):
        return list(self._order)

    def entries(self):
        """Every entry, in insertion order."""
        return [self._entries[entry_id].copy() for entry_id in self._order]

    def by_tag(self, tag):
        return [self._entries[entry_id].copy() for entry_id in self._tags.ids_for(normalize_tag(tag))]

    def by_all_tags(self, tags):
        wanted = [normalize_tag(tag) for tag in tags]
        return [self._entries[entry_id].copy() for entry_id in self._tags.ids_for_all(wanted)]

    def tags(self):
        return self._tags.tags()

    def tag_counts(self):
        return self._tags.counts()

    def rebuild_tag_index(self):
        self._tags.rebuild(self._entries[entry_id] for entry_id in self._order)

    def __len__(self):
        return len(self._order)

    def __contains__(self, entry_id):
        return entry_id in self._entries

    def __iter__(self):
        return iter(self.entries())

    def __repr__(self):
        return "Depot(entries=%d, tags=%d)" % (len(self._order), len(self._tags))
