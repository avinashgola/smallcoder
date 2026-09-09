"""What a caller is asking for, independent of how it will be found.

Every condition can answer :meth:`Condition.matches` for a single row.
That is the definition of the condition; the planner in
:mod:`finders.planner` is only allowed to use an index when the index
returns the same rows the definition would.
"""

from sheets.errors import TableError


class Condition:
    """Base class; subclasses implement :meth:`matches`."""

    def matches(self, row):
        raise NotImplementedError

    def columns(self):
        return []

    def __call__(self, row):
        return self.matches(row)

    def __and__(self, other):
        return EveryOf([self, other])

    def __or__(self, other):
        return AnyOf([self, other])

    def __invert__(self):
        return Negate(self)


class ColumnCondition(Condition):
    def __init__(self, column):
        if not isinstance(column, str) or not column:
            raise TableError("conditions need a column name")
        self.column = column

    def columns(self):
        return [self.column]

    def value_of(self, row):
        return row.get(self.column)


class Equals(ColumnCondition):
    """``column == value``."""

    def __init__(self, column, value):
        super().__init__(column)
        self.value = value

    def matches(self, row):
        return self.value_of(row) == self.value

    def __repr__(self):
        return "Equals(%r, %r)" % (self.column, self.value)


class OneOf(ColumnCondition):
    """``column`` holds any of ``values``."""

    def __init__(self, column, values):
        super().__init__(column)
        self.values = list(values)

    def matches(self, row):
        return self.value_of(row) in self.values

    def __repr__(self):
        return "OneOf(%r, %r)" % (self.column, self.values)


class InRange(ColumnCondition):
    """``low <= column <= high``.

    The range is closed: a row whose value is exactly ``low`` or exactly
    ``high`` is part of the answer.  Empty cells never match, because
    ``None`` does not sit anywhere on the scale.
    """

    def __init__(self, column, low, high):
        super().__init__(column)
        if low > high:
            raise TableError("range %r..%r is inside out" % (low, high))
        self.low = low
        self.high = high

    def matches(self, row):
        value = self.value_of(row)
        if value is None:
            return False
        return self.low <= value <= self.high

    def __repr__(self):
        return "InRange(%r, %r, %r)" % (self.column, self.low, self.high)


class AtLeast(ColumnCondition):
    """``low <= column``."""

    def __init__(self, column, low):
        super().__init__(column)
        self.low = low

    def matches(self, row):
        value = self.value_of(row)
        return value is not None and self.low <= value

    def __repr__(self):
        return "AtLeast(%r, %r)" % (self.column, self.low)


class AtMost(ColumnCondition):
    """``column <= high``."""

    def __init__(self, column, high):
        super().__init__(column)
        self.high = high

    def matches(self, row):
        value = self.value_of(row)
        return value is not None and value <= self.high

    def __repr__(self):
        return "AtMost(%r, %r)" % (self.column, self.high)


class Matches(ColumnCondition):
    """Case-insensitive substring test against a text column."""

    def __init__(self, column, fragment):
        super().__init__(column)
        self.fragment = fragment

    def matches(self, row):
        value = self.value_of(row)
        if not isinstance(value, str):
            return False
        return self.fragment.lower() in value.lower()

    def __repr__(self):
        return "Matches(%r, %r)" % (self.column, self.fragment)


class Group(Condition):
    def __init__(self, parts):
        self.parts = list(parts)
        if not self.parts:
            raise TableError("a group needs at least one condition")
        for part in self.parts:
            if not isinstance(part, Condition):
                raise TableError("expected a condition, got %r" % (part,))

    def columns(self):
        names = []
        for part in self.parts:
            for name in part.columns():
                if name not in names:
                    names.append(name)
        return names

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)


class EveryOf(Group):
    """True when every part is true."""

    def matches(self, row):
        return all(part.matches(row) for part in self.parts)


class AnyOf(Group):
    """True when at least one part is true."""

    def matches(self, row):
        return any(part.matches(row) for part in self.parts)


class Negate(Condition):
    def __init__(self, part):
        if not isinstance(part, Condition):
            raise TableError("expected a condition, got %r" % (part,))
        self.part = part

    def matches(self, row):
        return not self.part.matches(row)

    def columns(self):
        return self.part.columns()

    def __repr__(self):
        return "Negate(%r)" % (self.part,)
