"""One declared field: its type and the constraints that apply to it."""

from . import rules

KINDS = {"str": str, "int": int, "bool": bool}


class Field:
    """A single entry in a schema.

    Constraints are checked in the order they are listed below and the first
    problem found is the one reported for the field.
    """

    def __init__(self, name, kind="str", required=True, min_length=None,
                 max_length=None, minimum=None, maximum=None, choices=(),
                 email=False):
        if kind not in KINDS:
            raise ValueError(f"{name}: unknown kind {kind!r}")
        self.name = name
        self.kind = kind
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.minimum = minimum
        self.maximum = maximum
        self.choices = tuple(choices)
        self.email = email

    def check_type(self, value):
        if self.kind == "int" and isinstance(value, bool):
            return "must be a whole number"
        if not isinstance(value, KINDS[self.kind]):
            return f"must be a {self.kind}"
        return None

    def check(self, value):
        """The first problem with ``value``, or ``None`` if there is none."""
        problem = self.check_type(value)
        if problem is not None:
            return problem
        if self.kind == "str":
            problem = rules.not_blank(value)
            if problem is None and self.min_length is not None:
                problem = rules.min_length(value, self.min_length)
            if problem is None and self.max_length is not None:
                problem = rules.max_length(value, self.max_length)
            if problem is None and self.email:
                problem = rules.looks_like_email(value)
        elif self.kind == "int":
            if self.minimum is not None:
                problem = rules.minimum(value, self.minimum)
            if problem is None and self.maximum is not None:
                problem = rules.maximum(value, self.maximum)
        if problem is None and self.choices:
            problem = rules.one_of(value, self.choices)
        return problem

    def __repr__(self):
        return f"Field({self.name!r}, kind={self.kind!r})"
