"""Predicate objects used to filter records.

Every predicate answers ``matches(record)`` and reports the fields it
reads through ``fields()``, which lets the engine decide whether an index
could help.  Predicates compose with ``&``, ``|`` and ``~``.
"""

from catalog.errors import QueryError


class Predicate:
    """Base class; subclasses implement :meth:`matches`."""

    def matches(self, record):
        raise NotImplementedError

    def fields(self):
        return []

    def __call__(self, record):
        return self.matches(record)

    def __and__(self, other):
        return All([self, other])

    def __or__(self, other):
        return Any([self, other])

    def __invert__(self):
        return Not(self)


class Always(Predicate):
    """Matches every record; the identity of :class:`All`."""

    def matches(self, record):
        return True

    def __repr__(self):
        return "Always()"


class FieldPredicate(Predicate):
    """Base for predicates that look at a single field."""

    def __init__(self, field):
        if not isinstance(field, str) or not field:
            raise QueryError("field names must be non-empty strings")
        self.field = field

    def fields(self):
        return [self.field]

    def value_of(self, record):
        return record.get(self.field)


class Eq(FieldPredicate):
    def __init__(self, field, value):
        super().__init__(field)
        self.value = value

    def matches(self, record):
        return self.value_of(record) == self.value

    def __repr__(self):
        return "Eq(%r, %r)" % (self.field, self.value)


class Ne(FieldPredicate):
    def __init__(self, field, value):
        super().__init__(field)
        self.value = value

    def matches(self, record):
        return self.value_of(record) != self.value

    def __repr__(self):
        return "Ne(%r, %r)" % (self.field, self.value)


class In(FieldPredicate):
    def __init__(self, field, values):
        super().__init__(field)
        self.values = list(values)

    def matches(self, record):
        return self.value_of(record) in self.values

    def __repr__(self):
        return "In(%r, %r)" % (self.field, self.values)


class Between(FieldPredicate):
    """``low <= value <= high``, with either bound optional."""

    def __init__(self, field, low=None, high=None):
        super().__init__(field)
        self.low = low
        self.high = high

    def matches(self, record):
        value = self.value_of(record)
        if value is None:
            return False
        if self.low is not None and value < self.low:
            return False
        if self.high is not None and value > self.high:
            return False
        return True

    def __repr__(self):
        return "Between(%r, %r, %r)" % (self.field, self.low, self.high)


class Compare(FieldPredicate):
    """One of ``<``, ``<=``, ``>`` or ``>=`` against a fixed bound."""

    OPERATORS = {
        "lt": lambda value, bound: value < bound,
        "lte": lambda value, bound: value <= bound,
        "gt": lambda value, bound: value > bound,
        "gte": lambda value, bound: value >= bound,
    }

    def __init__(self, field, operator, bound):
        super().__init__(field)
        if operator not in self.OPERATORS:
            raise QueryError("unknown comparison %r" % (operator,))
        self.operator = operator
        self.bound = bound

    def matches(self, record):
        value = self.value_of(record)
        if value is None:
            return False
        try:
            return self.OPERATORS[self.operator](value, self.bound)
        except TypeError:
            return False

    def __repr__(self):
        return "Compare(%r, %r, %r)" % (self.field, self.operator, self.bound)


class Contains(FieldPredicate):
    """Substring match for text, membership for lists."""

    def __init__(self, field, needle, case_sensitive=False):
        super().__init__(field)
        self.needle = needle
        self.case_sensitive = case_sensitive

    def matches(self, record):
        value = self.value_of(record)
        if isinstance(value, str) and isinstance(self.needle, str):
            if self.case_sensitive:
                return self.needle in value
            return self.needle.lower() in value.lower()
        if isinstance(value, (list, tuple)):
            return self.needle in value
        return False

    def __repr__(self):
        return "Contains(%r, %r)" % (self.field, self.needle)


class StartsWith(FieldPredicate):
    def __init__(self, field, prefix):
        super().__init__(field)
        self.prefix = prefix

    def matches(self, record):
        value = self.value_of(record)
        return isinstance(value, str) and value.lower().startswith(self.prefix.lower())

    def __repr__(self):
        return "StartsWith(%r, %r)" % (self.field, self.prefix)


class Present(FieldPredicate):
    """The field exists and is not ``None``."""

    def matches(self, record):
        return record.get(self.field) is not None

    def __repr__(self):
        return "Present(%r)" % (self.field,)


class Combinator(Predicate):
    def __init__(self, parts):
        self.parts = list(parts)
        for part in self.parts:
            if not isinstance(part, Predicate):
                raise QueryError("expected a predicate, got %r" % (part,))

    def fields(self):
        names = []
        for part in self.parts:
            for name in part.fields():
                if name not in names:
                    names.append(name)
        return names

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.parts)


class All(Combinator):
    """True when every part matches."""

    def matches(self, record):
        return all(part.matches(record) for part in self.parts)


class Any(Combinator):
    """True when at least one part matches."""

    def matches(self, record):
        return any(part.matches(record) for part in self.parts)


class Not(Predicate):
    def __init__(self, part):
        if not isinstance(part, Predicate):
            raise QueryError("expected a predicate, got %r" % (part,))
        self.part = part

    def matches(self, record):
        return not self.part.matches(record)

    def fields(self):
        return self.part.fields()

    def __repr__(self):
        return "Not(%r)" % (self.part,)
