"""What to keep when sifting entries.

Rules answer :meth:`Rule.holds` for a single entry.  They are written
against the :class:`~depot.entry.Entry` interface rather than against
dictionaries, so a rule works the same on a live depot and on entries
just read out of an archive.
"""

from depot.errors import FieldError
from depot.tags.tagset import normalize_tag


class Rule:
    """Base class; subclasses implement :meth:`holds`."""

    def holds(self, entry):
        raise NotImplementedError

    def __call__(self, entry):
        return self.holds(entry)

    def __and__(self, other):
        return Every([self, other])

    def __or__(self, other):
        return Some([self, other])

    def __invert__(self):
        return Unless(self)


class HasTag(Rule):
    """The entry carries ``tag``."""

    def __init__(self, tag):
        self.tag = normalize_tag(tag)

    def holds(self, entry):
        return entry.tags.holds(self.tag)

    def __repr__(self):
        return "HasTag(%r)" % (self.tag,)


class HasAllTags(Rule):
    """The entry carries every one of ``tags``."""

    def __init__(self, tags):
        self.tags = [normalize_tag(tag) for tag in tags]
        if not self.tags:
            raise FieldError("HasAllTags needs at least one tag")

    def holds(self, entry):
        return entry.tags.holds_all(self.tags)

    def __repr__(self):
        return "HasAllTags(%r)" % (self.tags,)


class FieldEquals(Rule):
    """The entry's ``name`` field is exactly ``value``.

    Comparison is by value, so a field holding ``0`` does not match a
    rule looking for ``False`` and an absent field matches neither.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def holds(self, entry):
        if not entry.has(self.name):
            return False
        held = entry.get(self.name)
        if isinstance(held, bool) != isinstance(self.value, bool):
            return False
        return held == self.value

    def __repr__(self):
        return "FieldEquals(%r, %r)" % (self.name, self.value)


class FieldPresent(Rule):
    """The entry has the field at all, whatever it holds."""

    def __init__(self, name):
        self.name = name

    def holds(self, entry):
        return entry.has(self.name)

    def __repr__(self):
        return "FieldPresent(%r)" % (self.name,)


class FieldMissing(Rule):
    """The entry does not have the field."""

    def __init__(self, name):
        self.name = name

    def holds(self, entry):
        return not entry.has(self.name)

    def __repr__(self):
        return "FieldMissing(%r)" % (self.name,)


class TextContains(Rule):
    """Case-insensitive substring test against a text field."""

    def __init__(self, name, fragment):
        self.name = name
        self.fragment = fragment

    def holds(self, entry):
        value = entry.get(self.name)
        if not isinstance(value, str):
            return False
        return self.fragment.lower() in value.lower()

    def __repr__(self):
        return "TextContains(%r, %r)" % (self.name, self.fragment)


class RevisionAtLeast(Rule):
    """The entry has been amended at least ``revision - 1`` times."""

    def __init__(self, revision):
        self.revision = revision

    def holds(self, entry):
        return entry.revision >= self.revision

    def __repr__(self):
        return "RevisionAtLeast(%r)" % (self.revision,)


class Group(Rule):
    def __init__(self, parts):
        self.parts = list(parts)
        if not self.parts:
            raise FieldError("a group needs at least one rule")
        for part in self.parts:
            if not isinstance(part, Rule):
                raise FieldError("expected a rule, got %r" % (part,))

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)


class Every(Group):
    """Every part holds."""

    def holds(self, entry):
        return all(part.holds(entry) for part in self.parts)


class Some(Group):
    """At least one part holds."""

    def holds(self, entry):
        return any(part.holds(entry) for part in self.parts)


class Unless(Rule):
    """The part does not hold."""

    def __init__(self, part):
        if not isinstance(part, Rule):
            raise FieldError("expected a rule, got %r" % (part,))
        self.part = part

    def holds(self, entry):
        return not self.part.holds(entry)

    def __repr__(self):
        return "Unless(%r)" % (self.part,)
