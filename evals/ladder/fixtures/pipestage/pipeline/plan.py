"""A plan is the declarative description of a pipeline."""

from common.errors import ConfigError
from common.strings import slugify
from common.validators import ensure_type, non_empty_string


class Plan:
    """An ordered list of stage configurations."""

    def __init__(self, name, stages, params=None):
        self.name = slugify(non_empty_string(name, "plan name"))
        ensure_type(stages, list, "stages", where=self.name)
        if not stages:
            raise ConfigError("a plan needs at least one stage", where=self.name)
        self.stages = [dict(stage) for stage in stages]
        self.params = dict(params or {})

    # -- reading ---------------------------------------------------------

    def stage_names(self):
        return [slugify(stage.get("name", "")) for stage in self.stages]

    def types_used(self):
        return sorted({stage.get("type") for stage in self.stages})

    def __len__(self):
        return len(self.stages)

    # -- editing ---------------------------------------------------------

    def with_stage(self, config, position=None):
        """A copy with one more stage, appended or inserted."""
        stages = list(self.stages)
        if position is None:
            stages.append(dict(config))
        else:
            stages.insert(position, dict(config))
        return Plan(self.name, stages, self.params)

    def without_stage(self, name):
        target = slugify(name)
        stages = [s for s in self.stages if slugify(s.get("name", "")) != target]
        if len(stages) == len(self.stages):
            raise ConfigError("no stage named %r" % (name,), where=self.name)
        return Plan(self.name, stages, self.params)

    # -- checks ----------------------------------------------------------

    def validate(self, registry=None):
        """Check names and, when a registry is given, the stage types."""
        seen = set()
        for index, stage in enumerate(self.stages):
            where = "%s[%d]" % (self.name, index)
            if "name" not in stage or "type" not in stage:
                raise ConfigError("stage needs both 'name' and 'type'", where=where)
            name = slugify(stage["name"])
            if not name:
                raise ConfigError("stage name is empty", where=where)
            if name in seen:
                raise ConfigError("duplicate stage name %r" % (name,), where=where)
            seen.add(name)
            if registry is not None and not registry.knows(stage["type"]):
                raise ConfigError(
                    "unknown stage type %r" % (stage["type"],), where=where
                )
        return self

    @classmethod
    def from_dict(cls, data):
        ensure_type(data, dict, "plan")
        return cls(
            data.get("name", "pipeline"),
            data.get("stages", []),
            data.get("params"),
        )

    def describe(self):
        return "%s: %s" % (self.name, " -> ".join(self.stage_names()))
