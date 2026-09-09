"""Jitter sources.

Backoff jitter needs a source of numbers in [0, 1). Production uses the
standard library; tests hand in one of the deterministic sources below so the
computed delays are exact.
"""

import random


def system_random():
    """Default jitter source."""
    return random.random()


class ConstantJitter:
    """Always returns the same ratio."""

    def __init__(self, value=0.5):
        if not 0.0 <= value < 1.0:
            raise ValueError("jitter ratio must be in [0, 1)")
        self.value = float(value)

    def __call__(self):
        return self.value


class CycleJitter:
    """Walks a fixed list of ratios, repeating when it runs out."""

    def __init__(self, values):
        values = [float(value) for value in values]
        if not values:
            raise ValueError("need at least one jitter value")
        for value in values:
            if not 0.0 <= value < 1.0:
                raise ValueError("jitter ratio must be in [0, 1)")
        self.values = values
        self._index = 0

    def __call__(self):
        value = self.values[self._index % len(self.values)]
        self._index += 1
        return value

    def reset(self):
        self._index = 0
