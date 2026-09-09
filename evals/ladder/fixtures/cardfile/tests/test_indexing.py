import pytest

from catalog.errors import DuplicateKey, QueryError
from catalog.indexing import HashIndex, IndexRegistry, UniqueIndex, index_key
from catalog.indexing.keys import MISSING, describe_key, keys_for


def test_hash_index_groups_ids_by_key():
    index = HashIndex("status")
    index.add("rec-0001", {"status": "open"})
    index.add("rec-0002", {"status": "open"})
    index.add("rec-0003", {"status": "done"})
    assert index.lookup("open") == ["rec-0001", "rec-0002"]
    assert index.lookup("done") == ["rec-0003"]
    assert index.cardinality() == 2
    assert len(index) == 3


def test_hash_index_drops_empty_buckets():
    index = HashIndex("status")
    index.add("rec-0001", {"status": "open"})
    index.remove("rec-0001", {"status": "open"})
    assert "open" not in index
    assert index.keys() == []


def test_removing_an_unheld_key_is_harmless():
    index = HashIndex("status")
    index.add("rec-0001", {"status": "open"})
    index.remove("rec-0001", {"status": "done"})
    assert index.lookup("open") == ["rec-0001"]


def test_multi_valued_index_fans_a_list_out():
    index = HashIndex("tags", multi=True)
    index.add("rec-0001", {"tags": ["urgent", "outdoor"]})
    index.add("rec-0002", {"tags": ["outdoor"]})
    assert index.lookup("outdoor") == ["rec-0001", "rec-0002"]
    assert index.lookup("urgent") == ["rec-0001"]


def test_missing_fields_share_one_key():
    assert keys_for({}, "owner") == [MISSING]
    assert keys_for({"owner": None}, "owner") == [MISSING]
    assert keys_for({"tags": []}, "tags", multi=True) == [MISSING]


def test_index_key_normalises_values():
    assert index_key("  open ") == "open"
    assert index_key(["a", "b"]) == ("a", "b")
    assert index_key({"b": 1, "a": 2}) == (("a", 2), ("b", 1))
    assert describe_key(MISSING) == "<missing>"


def test_unique_index_rejects_a_second_holder():
    index = UniqueIndex("code")
    index.add("rec-0001", {"code": "A-1"})
    with pytest.raises(DuplicateKey):
        index.add("rec-0002", {"code": "A-1"})
    assert index.holder("A-1") == "rec-0001"


def test_unique_index_ignores_records_without_the_field():
    index = UniqueIndex("code")
    index.add("rec-0001", {})
    index.add("rec-0002", {})
    assert index.keys() == []


def test_registry_reindex_moves_a_record_between_keys():
    registry = IndexRegistry()
    registry.add("status")
    before = {"status": "open"}
    after = {"status": "done"}
    registry.index_record("rec-0001", before)
    registry.reindex("rec-0001", before, after)
    assert registry.lookup("status", "done") == ["rec-0001"]
    assert registry.lookup("status", "open") == []


def test_registry_refuses_a_duplicate_definition():
    registry = IndexRegistry()
    registry.add("status")
    with pytest.raises(QueryError):
        registry.add("status")
    with pytest.raises(QueryError):
        registry.lookup("owner", "ana")


def test_registry_rebuild_starts_from_scratch():
    registry = IndexRegistry()
    registry.add("status")
    registry.index_record("rec-0001", {"status": "open"})
    registry.rebuild([("rec-0002", {"status": "done"})])
    assert registry.lookup("status", "open") == []
    assert registry.summary() == {"status": 1}
