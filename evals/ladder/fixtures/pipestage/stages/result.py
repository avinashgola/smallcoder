"""What a stage hands back once it has processed a batch."""

from common.numbers import percent


class StageResult:
    """Records leaving a stage plus the counters describing the pass."""

    def __init__(self, stage, records, count_in, stats=None, notes=()):
        self.stage = stage
        self.records = list(records)
        self.count_in = int(count_in)
        self.stats = dict(stats or {})
        self.notes = list(notes)

    @property
    def count_out(self):
        return len(self.records)

    @property
    def dropped(self):
        return max(0, self.count_in - self.count_out)

    @property
    def kept_percent(self):
        return percent(self.count_out, self.count_in)

    def stat(self, name, default=0):
        return self.stats.get(name, default)

    def as_row(self):
        return (self.stage, self.count_in, self.count_out, self.dropped)

    def describe(self):
        return "%s: %d in, %d out (%g%% kept)" % (
            self.stage,
            self.count_in,
            self.count_out,
            self.kept_percent,
        )

    def __repr__(self):
        return "StageResult(%r, %d -> %d)" % (
            self.stage,
            self.count_in,
            self.count_out,
        )
