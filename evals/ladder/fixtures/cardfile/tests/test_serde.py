import pytest

from catalog import Store
from catalog.errors import SchemaError
from serde import dump, dumps, load, loads, snapshot_summary
from serde.values import decode_value, encode_value


def build_store():
    store = Store()
    store.add_index("status")
    store.add_index("code", unique=True)
    store.insert({"title": "Bleed the radiators", "status": "open", "code": "A-1"})
    store.insert({"title": "Fix the gate", "status": "done", "code": "A-2", "tags": ["outdoor"]})
    return store


def test_round_trip_keeps_records_and_ids():
    store = build_store()
    restored = load(dump(store))
    assert restored.items() == store.items()
    assert restored.ids() == store.ids()


def test_round_trip_keeps_indexes_working():
    store = build_store()
    restored = loads(dumps(store))
    assert restored.indexed_fields() == store.indexed_fields()
    assert restored.find_ids("status", "open") == store.find_ids("status", "open")


def test_ids_carry_over_without_colliding():
    store = build_store()
    restored = load(dump(store))
    fresh = restored.insert({"title": "Sand the deck"})
    assert fresh not in store.ids()


def test_tuples_and_sets_survive_the_trip():
    assert decode_value(encode_value(("a", 1))) == ("a", 1)
    assert decode_value(encode_value({"a", "b"})) == {"a", "b"}
    assert encode_value({"n": [1, 2]}) == {"n": [1, 2]}


def test_summary_describes_a_snapshot():
    payload = dump(build_store())
    assert snapshot_summary(payload) == "version 1, 2 record(s), 2 index(es)"


def test_a_snapshot_from_the_future_is_refused():
    payload = dump(build_store())
    payload["version"] = 99
    with pytest.raises(SchemaError):
        load(payload)


def test_records_may_not_use_the_reserved_tag():
    with pytest.raises(SchemaError):
        encode_value({"$type": "tuple"})
