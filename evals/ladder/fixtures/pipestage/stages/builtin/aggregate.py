"""Stages that collapse many records into fewer."""

from common.numbers import as_number, round_to
from common.records import Record
from common.validators import non_empty_string
from stages.base import Stage


class GroupSumStage(Stage):
    """Group by one field and sum another, emitting one record per group."""

    kind = "group_sum"

    def __init__(self, name, group_by, value_field, into=None):
        super().__init__(name)
        self.group_by = non_empty_string(group_by, "group_by", where=name)
        self.value_field = non_empty_string(value_field, "value_field", where=name)
        self.into = into or ("total_" + self.value_field)

    def process(self, records, ctx):
        totals = {}
        order = []
        for record in records:
            key = record.get(self.group_by)
            if key not in totals:
                totals[key] = 0.0
                order.append(key)
            totals[key] += as_number(record.get(self.value_field))
        ctx.put_artifact(self.name + "_groups", len(order))
        return [
            Record({self.group_by: key, self.into: round_to(totals[key])})
            for key in order
        ]

    def stats(self, records_in, records_out):
        return {"groups": len(records_out)}


class CountStage(Stage):
    """Pass records through untouched, recording how many there were."""

    kind = "count"

    def __init__(self, name, into="count"):
        super().__init__(name)
        self.into = non_empty_string(into, "into", where=name)

    def process(self, records, ctx):
        ctx.put_artifact(self.into, len(records))
        return list(records)

    def stats(self, records_in, records_out):
        return {"counted": len(records_in)}
