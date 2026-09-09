"""Delay calculation between retries.

`Backoff.delay_for` is called with the number of attempts that have already
been made, so the delay after the very first failure is the base delay.
"""

from support.rng import system_random


class Backoff:
    """Capped exponential backoff with optional proportional jitter."""

    def __init__(self, base=0.5, factor=2.0, cap=30.0, jitter=0.0, rand=None):
        if base < 0:
            raise ValueError("base delay cannot be negative")
        if factor < 1:
            raise ValueError("factor must be at least 1")
        if cap < base:
            raise ValueError("cap cannot be smaller than the base delay")
        if not 0.0 <= jitter <= 1.0:
            raise ValueError("jitter must be a ratio between 0 and 1")
        self.base = float(base)
        self.factor = float(factor)
        self.cap = float(cap)
        self.jitter = float(jitter)
        self.rand = rand or system_random

    def raw_delay(self, attempts_made):
        """The uncapped, unjittered delay after `attempts_made` failures."""
        if attempts_made < 1:
            raise ValueError("attempts_made starts at 1")
        return self.base * (self.factor ** (attempts_made - 1))

    def delay_for(self, attempts_made):
        """The delay to wait before the next attempt."""
        delay = min(self.raw_delay(attempts_made), self.cap)
        if self.jitter:
            delay -= delay * self.jitter * self.rand()
        return round(max(delay, 0.0), 6)

    def series(self, count):
        """The first `count` delays, for previewing a policy."""
        return [self.delay_for(number) for number in range(1, count + 1)]

    def describe(self):
        text = "base %gs, factor %g, cap %gs" % (self.base, self.factor, self.cap)
        if self.jitter:
            text += ", jitter %g" % self.jitter
        return text


NO_BACKOFF = Backoff(base=0.0, factor=1.0, cap=0.0)
