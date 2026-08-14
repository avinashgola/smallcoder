from ratelimit import DEFAULTS, build_limits, is_allowed


def test_defaults_returned():
    assert build_limits() == {"max_requests": 100, "window_seconds": 60, "burst": 10}


def test_overrides_applied():
    limits = build_limits({"max_requests": 5})
    assert limits["max_requests"] == 5
    assert limits["window_seconds"] == 60


def test_defaults_not_mutated_by_overrides():
    build_limits({"max_requests": 5})
    assert DEFAULTS["max_requests"] == 100


def test_later_calls_are_unaffected_by_earlier_overrides():
    build_limits({"max_requests": 5, "burst": 0})
    assert build_limits() == {"max_requests": 100, "window_seconds": 60, "burst": 10}


def test_is_allowed():
    limits = build_limits()
    assert is_allowed(110, limits)
    assert not is_allowed(111, limits)
