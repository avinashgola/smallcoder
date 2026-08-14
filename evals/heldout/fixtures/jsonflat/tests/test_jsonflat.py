import pytest

from jsonflat import flatten, get_path

NESTED = {
    "name": "svc",
    "db": {"host": "localhost", "port": 5432},
    "cache": {"redis": {"host": "cache-1", "ttl": 30}},
}


def test_top_level_keys_kept():
    assert flatten(NESTED)["name"] == "svc"


def test_nested_keys_are_prefixed():
    flat = flatten(NESTED)
    assert flat["db.host"] == "localhost"
    assert flat["db.port"] == 5432


def test_deeply_nested_keys_are_fully_prefixed():
    flat = flatten(NESTED)
    assert flat["cache.redis.host"] == "cache-1"
    assert flat["cache.redis.ttl"] == 30


def test_no_bare_keys_leak_from_nested_levels():
    flat = flatten(NESTED)
    assert "host" not in flat
    assert "port" not in flat


def test_collision_between_branches_is_avoided():
    data = {"a": {"x": 1}, "b": {"x": 2}}
    assert flatten(data) == {"a.x": 1, "b.x": 2}


def test_custom_separator():
    assert flatten({"a": {"b": 1}}, sep="/") == {"a/b": 1}


def test_get_path():
    assert get_path(NESTED, "cache.redis.ttl") == 30
    with pytest.raises(KeyError):
        get_path(NESTED, "cache.missing")
