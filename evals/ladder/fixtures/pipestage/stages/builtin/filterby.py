"""Stages that drop records, recording what they threw away.

Anything a filter rejects is appended to the run's `rejected` artifact so the
report can show why a run produced fewer rows than it was given.
"""

from common.numbers import as_number
from common.validators import non_empty_string, one_of
from stages.base import RecordStage

COMPARISONS = {
    "eq": lambda left, right: left == right,
    "ne": lambda left, right: left != right,
    "gt": lambda left, right: as_number(left) > as_number(right),
    "gte": lambda left, right: as_number(left) >= as_number(right),
    "lt": lambda left, right: as_number(left) < as_number(right),
    "lte": lambda left, right: as_number(left) <= as_number(right),
    "contains": lambda left, right: str(right) in str(left),
}


class FilterStage(RecordStage):
    """Keep records whose field satisfies a comparison."""

    kind = "filter"

    def __init__(self, name, field, op="eq", value=None, keep_missing=False):
        super().__init__(name)
        self.field = non_empty_string(field, "field", where=name)
        self.op = one_of(op, COMPARISONS, "op", where=name)
        self.value = value
        self.keep_missing = bool(keep_missing)

    def handle(self, record, ctx):
        if self.field not in record:
            if self.keep_missing:
                return record
            return self._reject(record, ctx, "no field %r" % (self.field,))
        if COMPARISONS[self.op](record[self.field], self.value):
            return record
        return self._reject(record, ctx, "%s %s %r" % (self.field, self.op, self.value))

    def _reject(self, record, ctx, reason):
        ctx.append_artifact("rejected", record)
        ctx.append_artifact("reject_reasons", "%s: %s" % (self.name, reason))
        return None

    def stats(self, records_in, records_out):
        return {"op": self.op, "field": self.field}


class RequireFieldsStage(RecordStage):
    """Drop records that are missing any of the required fields."""

    kind = "require"

    def __init__(self, name, fields):
        super().__init__(name)
        if not fields:
            raise ValueError("require needs at least one field")
        self.fields = [non_empty_string(field, "field", where=name) for field in fields]

    def handle(self, record, ctx):
        missing = [field for field in self.fields if field not in record]
        if missing:
            ctx.append_artifact("rejected", record)
            ctx.append_artifact(
                "reject_reasons",
                "%s: missing %s" % (self.name, ", ".join(missing)),
            )
            return None
        return record

    def stats(self, records_in, records_out):
        return {"required": len(self.fields)}
