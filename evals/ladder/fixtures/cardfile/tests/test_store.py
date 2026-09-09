import pytest

from catalog import DuplicateKey, RecordNotFound, Store


def make_store():
    store = Store()
    store.add_index("status")
    store.add_index("owner")
    return store


def test_insert_and_get_round_trip():
    store = Store()
    rid = store.insert({"title": "Wire the porch light", "status": "open"})
    assert store.get(rid) == {"title": "Wire the porch light", "status": "open"}
    assert len(store) == 1
    assert rid in store


def test_records_handed_out_are_copies():
    store = Store()
    rid = store.insert({"title": "Sand the deck", "tags": ["outdoor"]})
    borrowed = store.get(rid)
    borrowed["title"] = "changed"
    borrowed["tags"].append("indoor")
    assert store.get(rid)["title"] == "Sand the deck"
    assert store.get(rid)["tags"] == ["outdoor"]


def test_update_only_touches_named_fields():
    store = make_store()
    rid = store.insert({"title": "Bleed the radiators", "status": "open", "owner": "ana"})
    updated = store.update(rid, {"status": "done"})
    assert updated["title"] == "Bleed the radiators"
    assert updated["owner"] == "ana"
    assert updated["status"] == "done"


def test_update_moves_the_record_off_its_old_key():
    store = make_store()
    rid = store.insert({"title": "Bleed the radiators", "status": "open", "owner": "ana"})
    store.update(rid, {"status": "done"})
    assert store.find_ids("status", "done") == [rid]
    assert store.find_ids("status", "open") == []


def test_lookup_agrees_with_a_plain_scan():
    store = make_store()
    first = store.insert({"title": "Bleed the radiators", "status": "open"})
    second = store.insert({"title": "Fix the gate", "status": "open"})
    store.update(first, {"status": "done"})
    scanned = [row["title"] for row in store.all() if row["status"] == "open"]
    looked_up = [row["title"] for row in store.find("status", "open")]
    assert looked_up == scanned
    assert looked_up == ["Fix the gate"]
    assert second in store


def test_a_freed_unique_key_can_be_reused():
    store = Store()
    store.add_index("code", unique=True)
    first = store.insert({"code": "A-1", "title": "Bleed the radiators"})
    store.update(first, {"code": "A-2"})
    second = store.insert({"code": "A-1", "title": "Fix the gate"})
    assert store.find_ids("code", "A-1") == [second]
    assert store.find_ids("code", "A-2") == [first]


def test_unique_index_still_rejects_a_live_key():
    store = Store()
    store.add_index("code", unique=True)
    store.insert({"code": "A-1"})
    with pytest.raises(DuplicateKey):
        store.insert({"code": "A-1"})


def test_replace_swaps_the_whole_record():
    store = make_store()
    rid = store.insert({"title": "Bleed the radiators", "status": "open", "owner": "ana"})
    store.replace(rid, {"title": "Bleed the radiators", "status": "done"})
    assert store.get(rid) == {"title": "Bleed the radiators", "status": "done"}
    assert store.find_ids("owner", "ana") == []


def test_delete_removes_the_record_and_its_keys():
    store = make_store()
    rid = store.insert({"title": "Fix the gate", "status": "open"})
    store.delete(rid)
    assert rid not in store
    assert store.find_ids("status", "open") == []
    with pytest.raises(RecordNotFound):
        store.get(rid)


def test_rebuild_indexes_matches_incremental_maintenance():
    store = make_store()
    ids = store.insert_many(
        [
            {"title": "Bleed the radiators", "status": "open", "owner": "ana"},
            {"title": "Fix the gate", "status": "open", "owner": "bo"},
            {"title": "Sand the deck", "status": "done", "owner": "ana"},
        ]
    )
    store.update(ids[0], {"status": "done", "owner": "bo"})
    before = store.index_summary()
    store.rebuild_indexes()
    assert store.index_summary() == before


def test_events_are_recorded_in_order():
    store = Store()
    rid = store.insert({"title": "Fix the gate"})
    store.update(rid, {"title": "Fix the side gate"})
    store.delete(rid)
    assert [kind for kind, _ in store.events.entries()] == ["inserted", "updated", "deleted"]


def test_update_of_an_unknown_id_is_an_error():
    store = Store()
    with pytest.raises(RecordNotFound):
        store.update("rec-9999", {"status": "done"})
