"""Stages that reshape individual records."""

from common.errors import ConfigError
from common.numbers import as_number, round_to
from common.strings import slugify, title_case
from common.validators import non_empty_string, one_of
from stages.base import RecordStage

TRANSFORMS = {
    "upper": lambda value: str(value).upper(),
    "lower": lambda value: str(value).lower(),
    "strip": lambda value: str(value).strip(),
    "slug": slugify,
    "title": title_case,
    "number": as_number,
    "round2": lambda value: round_to(as_number(value), 2),
}

REDUCERS = {
    "sum": lambda values: round_to(sum(values)),
    "max": lambda values: max(values) if values else 0.0,
    "min": lambda values: min(values) if values else 0.0,
}


class MapStage(RecordStage):
    """Apply a named transform to one field of every record."""

    kind = "map"

    def __init__(self, name, field, using="strip", skip_missing=True):
        super().__init__(name)
        self.field = non_empty_string(field, "field", where=name)
        self.using = one_of(using, TRANSFORMS, "using", where=name)
        self.skip_missing = bool(skip_missing)

    def handle(self, record, ctx):
        if self.field not in record:
            if self.skip_missing:
                ctx.append_artifact("untouched", record)
                return record
            raise ConfigError("field %r is missing" % (self.field,), where=self.name)
        return record.with_field(self.field, TRANSFORMS[self.using](record[self.field]))

    def stats(self, records_in, records_out):
        return {"transform": self.using, "field": self.field}


class RenameStage(RecordStage):
    """Rename fields according to a mapping."""

    kind = "rename"

    def __init__(self, name, mapping):
        super().__init__(name)
        if not isinstance(mapping, dict) or not mapping:
            raise ConfigError("rename needs a non-empty mapping", where=name)
        self.mapping = dict(mapping)

    def handle(self, record, ctx):
        return record.renamed(self.mapping)

    def stats(self, records_in, records_out):
        return {"renamed": len(self.mapping)}


class DeriveStage(RecordStage):
    """Add a field computed from other numeric fields of the same record."""

    kind = "derive"

    def __init__(self, name, target, sources, using="sum"):
        super().__init__(name)
        self.target = non_empty_string(target, "target", where=name)
        if not sources:
            raise ConfigError("derive needs at least one source field", where=name)
        self.sources = list(sources)
        self.using = one_of(using, REDUCERS, "using", where=name)

    def handle(self, record, ctx):
        values = [as_number(record.get(field)) for field in self.sources]
        return record.with_field(self.target, REDUCERS[self.using](values))

    def stats(self, records_in, records_out):
        return {"derived": self.target, "reducer": self.using}
