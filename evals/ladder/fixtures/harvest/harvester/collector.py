"""Folding a run's stage outcomes into one summary.

The collector is deliberately forgiving: a plan may be configured to keep
going after a stage fails, in which case the outcomes it is handed contain
both the failure and everything that ran after it. All of them belong in the
report - the failures so an operator can see what broke, the rest so the row
counts and timings describe the whole run rather than its first half.
"""

from execution.outcome import State
from harvester.errors import CollectError
from harvester.summary import RunSummary
from toolkit.counters import Tally
from toolkit.sorting import unique


class ResultCollector:
    """Builds a `RunSummary` out of the outcomes of one run."""

    def __init__(self, plan, run_id=None, warn_on_drop=0):
        self.plan = plan
        self.run_id = run_id or plan
        self.warn_on_drop = int(warn_on_drop)
        self.warnings = []

    # -- collecting ------------------------------------------------------

    def collect(self, outcomes):
        """Fold every outcome of one run into a sealed summary."""
        outcomes = self._checked(outcomes)
        summary = RunSummary(self.run_id, self.plan)
        self.warnings = []
        for outcome in outcomes:
            if outcome.state == State.SKIPPED:
                summary.add_skipped(outcome)
                continue
            if outcome.state == State.FAILED:
                summary.add_failure(outcome)
                return summary
            self._check_drop(outcome)
            summary.add_success(outcome)
        return summary.seal()

    def collect_many(self, runs):
        """Collect several runs; `runs` is an iterable of outcome lists."""
        summaries = []
        for index, outcomes in enumerate(runs, start=1):
            collector = ResultCollector(
                self.plan,
                run_id="%s-%03d" % (self.plan, index),
                warn_on_drop=self.warn_on_drop,
            )
            summaries.append(collector.collect(outcomes))
        return summaries

    # -- checks ----------------------------------------------------------

    def _checked(self, outcomes):
        outcomes = list(outcomes)
        if not outcomes:
            raise CollectError("a run must have at least one stage outcome")
        names = [outcome.stage for outcome in outcomes]
        if len(unique(names)) != len(names):
            raise CollectError("duplicate stage names: " + ", ".join(names))
        return outcomes

    def _check_drop(self, outcome):
        if self.warn_on_drop and outcome.dropped >= self.warn_on_drop:
            self.warnings.append(
                "%s dropped %d of %d rows" % (
                    outcome.stage,
                    outcome.dropped,
                    outcome.rows_in,
                )
            )

    # -- extras ----------------------------------------------------------

    def state_tally(self, outcomes):
        """How many stages ended in each state."""
        return Tally(outcomes, key=lambda outcome: outcome.state)

    def describe(self):
        return "collector for %s (run %s)" % (self.plan, self.run_id)
