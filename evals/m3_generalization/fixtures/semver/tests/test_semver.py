import pytest

from semver import is_newer, latest, parse_version


def test_simple_ordering():
    assert is_newer("2.0.0", "1.9.9")
    assert not is_newer("1.2.3", "1.2.4")


def test_double_digit_components():
    assert is_newer("1.10.0", "1.9.0")
    assert is_newer("1.2.10", "1.2.9")


def test_equal_versions_are_not_newer():
    assert not is_newer("1.2.3", "1.2.3")


def test_latest_picks_highest():
    assert latest(["1.9.0", "1.10.0", "1.2.3"]) == "1.10.0"


def test_malformed_versions_rejected():
    with pytest.raises(ValueError):
        parse_version("1.2")
    with pytest.raises(ValueError):
        parse_version("not.a.version")
