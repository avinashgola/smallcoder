"""Clocks and sleepers.

Nothing in this package calls `time` directly. The worker is handed a clock
and a sleeper so that a test can drive a whole retry sequence without waiting
for it, and so that recorded durations are reproducible.
"""

import time


def system_clock():
    """The default clock: a monotonic wall clock in seconds."""
    return time.monotonic()


def system_sleeper(seconds):
    """The default sleeper."""
    if seconds > 0:
        time.sleep(seconds)


class ManualClock:
    """A clock that only moves when something asks it to."""

    def __init__(self, start=0.0):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        if seconds < 0:
            raise ValueError("cannot move a clock backwards")
        self.now += float(seconds)
        return self.now


class RecordingSleeper:
    """Records every requested delay and advances a clock instead of waiting."""

    def __init__(self, clock=None):
        self.clock = clock
        self.delays = []

    def __call__(self, seconds):
        self.delays.append(round(float(seconds), 6))
        if self.clock is not None:
            self.clock.advance(seconds)

    @property
    def total(self):
        return round(sum(self.delays), 6)

    def __len__(self):
        return len(self.delays)
