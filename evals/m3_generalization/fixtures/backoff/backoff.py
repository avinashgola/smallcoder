"""Retry schedule computation for network clients."""

DEFAULT_BASE_DELAY = 0.5
DEFAULT_ATTEMPTS = 3


def retry_schedule(attempts=None, base_delay=None):
    """Return the list of delays (seconds) to wait before each retry.

    The delay doubles on every attempt. A base_delay of 0 means retry
    immediately with no waiting, which batch jobs rely on.
    """
    if attempts is None:
        attempts = DEFAULT_ATTEMPTS
    base_delay = base_delay or DEFAULT_BASE_DELAY
    return [round(base_delay * (2**i), 3) for i in range(attempts)]


def total_wait(attempts=None, base_delay=None):
    """Total time spent waiting across the whole retry schedule."""
    return round(sum(retry_schedule(attempts, base_delay)), 3)
