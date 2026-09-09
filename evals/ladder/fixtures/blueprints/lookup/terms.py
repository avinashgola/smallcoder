"""Terms: what to keep when searching a cabinet.

A term is asked about a *row* - a record with its ``id`` and ``kind``
folded in, as :meth:`~cabinet.drawer.Cabinet.rows` produces - so a term
can talk about the kind of a record as easily as about its fields.
"""

from blueprint.errors import BlueprintError


class Term:
    """Base class; subclasses implement :meth:`holds`."""

    def holds(self, row):
        raise NotImplementedError

    def __call__(self, row):
        return self.holds(row)

    def __and__(self, other):
        return Both([self, other])

    def __or__(self, other):
        return Either([self, other])

    def __invert__(self):
        return Unless(self)


class IsKind(Term):
    """The row is a record of ``kind``."""

    def __init__(self, kind):
        self.kind = kind

    def holds(self, row):
        return row.get("kind") == self.kind

    def __repr__(self):
        return "IsKind(%r)" % (self.kind,)


class ValueIs(Term):
    """A field holds exactly ``value``.

    Flags and numbers are kept apart: ``ValueIs("done", True)`` does not
    match a record whose ``done`` is the number 1.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def holds(self, row):
        if self.name not in row:
            return False
        held = row[self.name]
        if isinstance(held, bool) != isinstance(self.value, bool):
            return False
        return held == self.value

    def __repr__(self):
        return "ValueIs(%r, %r)" % (self.name, self.value)


class ValueOver(Term):
    """A number field is greater than ``bound``."""

    def __init__(self, name, bound):
        self.name = name
        self.bound = bound

    def holds(self, row):
        held = row.get(self.name)
        if isinstance(held, bool) or not isinstance(held, (int, float)):
            return False
        return held > self.bound

    def __repr__(self):
        return "ValueOver(%r, %r)" % (self.name, self.bound)


class Holds(Term):
    """A list field contains ``item``, or a map field has that key."""

    def __init__(self, name, item):
        self.name = name
        self.item = item

    def holds(self, row):
        held = row.get(self.name)
        if isinstance(held, (list, dict)):
            return self.item in held
        return False

    def __repr__(self):
        return "Holds(%r, %r)" % (self.name, self.item)


class WordIn(Term):
    """Case-insensitive substring test against a text field."""

    def __init__(self, name, fragment):
        self.name = name
        self.fragment = fragment

    def holds(self, row):
        held = row.get(self.name)
        if not isinstance(held, str):
            return False
        return self.fragment.lower() in held.lower()

    def __repr__(self):
        return "WordIn(%r, %r)" % (self.name, self.fragment)


class Blank(Term):
    """A field is empty: no value, empty text, or an empty container."""

    def __init__(self, name):
        self.name = name

    def holds(self, row):
        if self.name not in row:
            return True
        held = row[self.name]
        if held is None:
            return True
        if isinstance(held, (str, list, dict)):
            return len(held) == 0
        return False

    def __repr__(self):
        return "Blank(%r)" % (self.name,)


class Group(Term):
    def __init__(self, parts):
        self.parts = list(parts)
        if not self.parts:
            raise BlueprintError("a group needs at least one term")
        for part in self.parts:
            if not isinstance(part, Term):
                raise BlueprintError("expected a term, got %r" % (part,))

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)


class Both(Group):
    """Every part holds."""

    def holds(self, row):
        return all(part.holds(row) for part in self.parts)


class Either(Group):
    """At least one part holds."""

    def holds(self, row):
        return any(part.holds(row) for part in self.parts)


class Unless(Term):
    """The part does not hold."""

    def __init__(self, part):
        if not isinstance(part, Term):
            raise BlueprintError("expected a term, got %r" % (part,))
        self.part = part

    def holds(self, row):
        return not self.part.holds(row)

    def __repr__(self):
        return "Unless(%r)" % (self.part,)
