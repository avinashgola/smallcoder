"""The report a run hands back."""

from common.numbers import percent
from common.strings import pad


class RunReport:
    """Per-stage counters, the artifacts produced, and the final records."""

    HEADERS = ("stage", "in", "out", "dropped")

    def __init__(self, run_id, plan_name, results, records, artifacts, notes=()):
        self.run_id = run_id
        self.plan_name = plan_name
        self.results = list(results)
        self.records = list(records)
        self.artifacts = dict(artifacts)
        self.notes = list(notes)

    # -- counters --------------------------------------------------------

    @property
    def count_in(self):
        return self.results[0].count_in if self.results else 0

    @property
    def count_out(self):
        return len(self.records)

    @property
    def dropped(self):
        return max(0, self.count_in - self.count_out)

    @property
    def kept_percent(self):
        return percent(self.count_out, self.count_in)

    def rejected(self):
        """Records the filters threw away during this run."""
        return list(self.artifacts.get("rejected", ()))

    def reject_reasons(self):
        return list(self.artifacts.get("reject_reasons", ()))

    def result_for(self, stage_name):
        for result in self.results:
            if result.stage == stage_name:
                return result
        raise KeyError("no stage named %r in this run" % (stage_name,))

    def artifact(self, name, default=None):
        return self.artifacts.get(name, default)

    # -- rendering -------------------------------------------------------

    def rows(self):
        return [result.as_row() for result in self.results]

    def table(self):
        widths = (18, 5, 5, 7)
        lines = ["".join(pad(h, w) for h, w in zip(self.HEADERS, widths))]
        for row in self.rows():
            lines.append("".join(pad(cell, w) for cell, w in zip(row, widths)))
        return "\n".join(line.rstrip() for line in lines)

    def summary_line(self):
        return "%s/%s: %d in, %d out, %d rejected" % (
            self.plan_name,
            self.run_id,
            self.count_in,
            self.count_out,
            len(self.rejected()),
        )

    def describe(self):
        return "%s\n%s" % (self.summary_line(), self.table())

    def __repr__(self):
        return "RunReport(%r, %d stages)" % (self.run_id, len(self.results))
