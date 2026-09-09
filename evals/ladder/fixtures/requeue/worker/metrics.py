"""Counters the worker keeps while it drains a queue."""


class Metrics:
    """Named counters plus a small set of accumulated durations."""

    def __init__(self):
        self._counters = {}
        self._timers = {}

    def incr(self, name, amount=1):
        self._counters[name] = self._counters.get(name, 0) + amount
        return self._counters[name]

    def observe(self, name, seconds):
        bucket = self._timers.setdefault(name, [])
        bucket.append(float(seconds))
        return bucket

    def get(self, name, default=0):
        return self._counters.get(name, default)

    def total(self, name):
        return round(sum(self._timers.get(name, ())), 6)

    def mean(self, name):
        values = self._timers.get(name, ())
        if not values:
            return 0.0
        return round(sum(values) / len(values), 6)

    def snapshot(self):
        data = dict(self._counters)
        for name, values in self._timers.items():
            data[name + "_total"] = round(sum(values), 6)
        return data

    def describe(self):
        items = sorted(self.snapshot().items())
        return ", ".join("%s=%s" % (name, value) for name, value in items)
