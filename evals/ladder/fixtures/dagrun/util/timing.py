"""Timing helpers with an injectable clock so runs stay reproducible."""


class StepClock:
    """A clock that advances by a fixed step every time it is read."""

    def __init__(self, start=0.0, step=1.0):
        self.now = float(start)
        self.step = float(step)

    def __call__(self):
        value = self.now
        self.now += self.step
        return value


class Stopwatch:
    """Measures elapsed time against whatever clock it was handed."""

    def __init__(self, clock):
        self._clock = clock
        self._started = None
        self._stopped = None

    def start(self):
        self._started = self._clock()
        self._stopped = None
        return self

    def stop(self):
        if self._started is None:
            raise RuntimeError("stopwatch was never started")
        self._stopped = self._clock()
        return self.elapsed

    @property
    def elapsed(self):
        if self._started is None:
            return 0.0
        end = self._stopped if self._stopped is not None else self._clock()
        return round(end - self._started, 6)


def format_seconds(value):
    """Compact duration rendering for report tables."""
    if value < 1:
        return "%dms" % round(value * 1000)
    if value < 60:
        return "%.1fs" % value
    minutes, seconds = divmod(value, 60)
    return "%dm%02ds" % (int(minutes), int(seconds))
