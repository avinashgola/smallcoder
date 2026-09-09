"""Driving a whole plan and collecting the per-stage outcomes."""

from execution.errors import PlanError
from execution.stagerun import run_stage, skipped_outcome
from toolkit.timing import system_clock
from toolkit.sorting import unique

CONTINUE = "continue"
STOP = "stop"
MODES = (CONTINUE, STOP)


class Session:
    """One plan, run over and over, producing a list of outcomes each time."""

    def __init__(self, plan, stages, clock=None, on_error=CONTINUE):
        stages = list(stages)
        if not stages:
            raise PlanError("a plan needs at least one stage")
        names = [step.name for step in stages]
        if len(unique(names)) != len(names):
            raise PlanError("stage names must be unique: " + ", ".join(names))
        if on_error not in MODES:
            raise PlanError("on_error must be one of " + ", ".join(MODES))
        self.plan = plan
        self.stages = stages
        self.clock = system_clock if clock is None else clock
        self.on_error = on_error
        self.runs = 0

    # -- inspection ------------------------------------------------------

    def stage_names(self):
        return [step.name for step in self.stages]

    def __len__(self):
        return len(self.stages)

    def describe(self):
        return "%s: %s" % (self.plan, " -> ".join(self.stage_names()))

    # -- running ---------------------------------------------------------

    def run(self, rows):
        """Run every stage, returning one outcome per stage in plan order."""
        self.runs += 1
        outcomes = []
        current = list(rows)
        halted = False
        for step in self.stages:
            if halted:
                outcomes.append(skipped_outcome(step, rows_in=len(current)))
                continue
            current, outcome = run_stage(step, current, self.clock)
            outcomes.append(outcome)
            if outcome.failed and step.critical and self.on_error == STOP:
                halted = True
        return outcomes

    def run_id(self):
        return "%s-%03d" % (self.plan, self.runs)
