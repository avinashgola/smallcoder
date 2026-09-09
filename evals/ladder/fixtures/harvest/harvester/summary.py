"""The object a collector fills in.

A summary is built up stage by stage and then sealed. Sealing computes the
run wide totals out of everything that was recorded, so a summary that never
got sealed reports zeroes.
"""

from harvester.errors import NotSealed
from toolkit.timing import format_duration, rate_per_second, total_seconds


class RunSummary:
    """Per-run roll-up of stage outcomes."""

    def __init__(self, run_id, plan):
        self.run_id = run_id
        self.plan = plan
        self.outcomes = []
        self.succeeded = []
        self.failed = []
        self.skipped = []
        self.rows_in = 0
        self.rows_out = 0
        self.duration = 0.0
        self.sealed = False

    # -- filling in ------------------------------------------------------

    def add_success(self, outcome):
        self.outcomes.append(outcome)
        self.succeeded.append(outcome)
        return outcome

    def add_failure(self, outcome):
        self.outcomes.append(outcome)
        self.failed.append(outcome)
        return outcome

    def add_skipped(self, outcome):
        self.outcomes.append(outcome)
        self.skipped.append(outcome)
        return outcome

    def seal(self):
        """Compute the run wide totals; call it once every stage is recorded."""
        self.duration = total_seconds(outcome.duration for outcome in self.outcomes)
        self.rows_in = self.outcomes[0].rows_in if self.outcomes else 0
        self.rows_out = self.succeeded[-1].rows_out if self.succeeded else 0
        self.sealed = True
        return self

    # -- reading ---------------------------------------------------------

    def recorded(self):
        """Every outcome, in the order the collector saw it."""
        return list(self.outcomes)

    @property
    def stage_count(self):
        return len(self.outcomes)

    @property
    def ok(self):
        return not self.failed

    def stage_names(self):
        return [outcome.stage for outcome in self.outcomes]

    def failed_names(self):
        return [outcome.stage for outcome in self.failed]

    def succeeded_names(self):
        return [outcome.stage for outcome in self.succeeded]

    def skipped_names(self):
        return [outcome.stage for outcome in self.skipped]

    def outcome_for(self, stage):
        for outcome in self.outcomes:
            if outcome.stage == stage:
                return outcome
        raise KeyError("no stage named %r in this summary" % (stage,))

    def require_sealed(self):
        if not self.sealed:
            raise NotSealed(self.run_id)
        return self

    @property
    def throughput(self):
        return rate_per_second(self.rows_out, self.duration)

    def summary_line(self):
        return "%s/%s: %d stage(s), %d ok, %d failed, %d skipped, %d rows in %s" % (
            self.plan,
            self.run_id,
            self.stage_count,
            len(self.succeeded),
            len(self.failed),
            len(self.skipped),
            self.rows_out,
            format_duration(self.duration),
        )

    def __repr__(self):
        return "RunSummary(%r, %d stages)" % (self.run_id, self.stage_count)
