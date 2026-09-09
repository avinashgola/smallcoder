"""Time: the clocks a run is driven by and the formatting of what it took.

Nothing in this project reads the wall clock directly; a clock is always passed
in, which is what makes recorded durations reproducible.
"""

import time


def system_clock():
    return time.monotonic()


class TickClock:
    """Advances by a fixed step on every read, so durations are exact."""

    def __init__(self, start=0.0, step=0.5):
        if step < 0:
            raise ValueError("step cannot be negative")
        self.now = float(start)
        self.step = float(step)
        self.reads = 0

    def __call__(self):
        value = self.now
        self.now += self.step
        self.reads += 1
        return value


class FrozenClock:
    """Never moves unless told to; useful when a duration must be zero."""

    def __init__(self, start=0.0):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += float(seconds)
        return self.now


def format_duration(seconds):
    """'0ms', '250ms', '1.5s', '2m05s'."""
    seconds = float(seconds)
    if seconds < 1:
        return "%dms" % round(seconds * 1000)
    if seconds < 60:
        return "%.1fs" % seconds
    minutes, rest = divmod(seconds, 60)
    return "%dm%02ds" % (int(minutes), int(rest))


def rate_per_second(count, seconds, places=1):
    """Rows per second, guarding against a zero duration."""
    if seconds <= 0:
        return 0.0
    return round(count / float(seconds), places)


def share(part, whole, places=1):
    if not whole:
        return 0.0
    return round(100.0 * part / float(whole), places)


def total_seconds(durations):
    return round(sum(float(value) for value in durations), 6)
