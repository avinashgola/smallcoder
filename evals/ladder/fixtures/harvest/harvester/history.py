"""Keeping several run summaries so trends are visible."""

from harvester.aggregate import merge
from toolkit.sorting import top_n
from toolkit.timing import share


class History:
    """An append-only list of summaries for one plan."""

    def __init__(self, plan, summaries=None):
        self.plan = plan
        self._summaries = list(summaries or [])

    def add(self, summary):
        if summary.plan != self.plan:
            raise ValueError(
                "summary for plan %r does not belong to %r" % (summary.plan, self.plan)
            )
        self._summaries.append(summary)
        return summary

    def summaries(self):
        return list(self._summaries)

    def latest(self):
        return self._summaries[-1] if self._summaries else None

    def run_ids(self):
        return [summary.run_id for summary in self._summaries]

    def clean_run_share(self):
        """Percentage of recorded runs with no failed stage."""
        clean = sum(1 for summary in self._summaries if summary.ok)
        return share(clean, len(self._summaries))

    def average_duration(self):
        if not self._summaries:
            return 0.0
        total = sum(summary.duration for summary in self._summaries)
        return round(total / len(self._summaries), 6)

    def slowest_runs(self, count=3):
        return top_n(self._summaries, key=lambda s: s.duration, count=count)

    def failing_stages(self):
        """Stage names that failed at least once, with how often."""
        counts = {}
        for summary in self._summaries:
            for name in summary.failed_names():
                counts[name] = counts.get(name, 0) + 1
        return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))

    def headline(self):
        return merge(self._summaries)

    def __len__(self):
        return len(self._summaries)
