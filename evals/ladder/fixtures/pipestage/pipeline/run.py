"""Executing the stages of a pipeline in order."""

from common.errors import ConfigError
from common.records import records_from
from pipeline.report import RunReport
from stages.context import StageContext


class Pipeline:
    """A named sequence of stages that can be run over and over."""

    def __init__(self, name, stages, params=None):
        if not stages:
            raise ConfigError("a pipeline needs at least one stage", where=name)
        self.name = name
        self.stages = list(stages)
        self.params = dict(params or {})
        self._runs = 0

    # -- inspection ------------------------------------------------------

    def stage_names(self):
        return [stage.name for stage in self.stages]

    def stage(self, name):
        for stage in self.stages:
            if stage.name == name:
                return stage
        raise KeyError("no stage named %r" % (name,))

    def __len__(self):
        return len(self.stages)

    # -- running ---------------------------------------------------------

    def next_run_id(self):
        self._runs += 1
        return "%s-%03d" % (self.name, self._runs)

    def make_context(self, params=None, run_id=None):
        """The context a run works with: parameters merged, artifacts empty."""
        merged = dict(self.params)
        merged.update(params or {})
        return StageContext(run_id or self.next_run_id(), params=merged)

    def run(self, rows, params=None, run_id=None):
        """Push `rows` through every stage and report on the pass."""
        ctx = self.make_context(params=params, run_id=run_id)
        records = records_from(rows)
        results = []
        for stage in self.stages:
            result = stage.run(records, ctx)
            results.append(result)
            records = result.records
        return RunReport(
            ctx.run_id,
            self.name,
            results,
            records,
            ctx.artifacts,
            notes=ctx.notes,
        )

    def run_batches(self, batches, params=None):
        """Run the same pipeline over several independent batches."""
        return [self.run(rows, params=params) for rows in batches]

    def describe(self):
        return "%s: %s" % (self.name, " -> ".join(self.stage_names()))
