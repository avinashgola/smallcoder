"""Rate-limit configuration."""

DEFAULTS = {"max_requests": 100, "window_seconds": 60, "burst": 10}


def build_limits(overrides=None):
    """Build a rate-limit config from DEFAULTS plus optional overrides."""
    limits = DEFAULTS
    if overrides:
        limits.update(overrides)
    return limits


def is_allowed(count, limits):
    """True when `count` requests is within the configured limit."""
    return count <= limits["max_requests"] + limits["burst"]
