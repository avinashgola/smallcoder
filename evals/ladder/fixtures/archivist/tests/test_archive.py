import json

import pytest

from archive import dump, dumps, load, loads
from archive.frames import check_frame, encode_value
from archive.manifest import describe, digest_of
from depot import Depot, Entry
from depot.errors import ArchiveError


def build_depot():
    depot = Depot()
    depot.add({"title": "Bleed the radiators", "minutes": 45}, tags=["home", "winter"])
    depot.add({"title": "Fix the gate", "minutes": 0, "done": False}, tags=["home"])
    depot.add({"title": "File the receipts", "note": "", "tags_seen": []}, tags=["admin"])
    depot.amend("e-0001", {"minutes": 50})
    return depot


def test_round_trip_returns_the_same_entries():
    depot = build_depot()
    restored = load(dump(depot))
    assert restored.entries() == depot.entries()
    assert restored.ids() == depot.ids()


def test_round_trip_through_text():
    depot = build_depot()
    restored = loads(dumps(depot))
    assert restored.entries() == depot.entries()
    assert restored.tag_counts() == depot.tag_counts()


def test_zero_and_empty_values_come_back():
    depot = build_depot()
    restored = loads(dumps(depot))
    second = restored.get("e-0002")
    assert second.get("minutes") == 0
    assert second.get("done") is False
    third = restored.get("e-0003")
    assert third.get("note") == ""
    assert third.get("tags_seen") == []


def test_an_absent_field_stays_absent():
    depot = build_depot()
    restored = loads(dumps(depot))
    assert not restored.get("e-0001").has("note")
    assert restored.get("e-0001").names() == ["minutes", "title"]


def test_every_frame_carries_the_entry_it_describes():
    depot = build_depot()
    frames = dump(depot)["entries"]
    assert [frame["id"] for frame in frames] == depot.ids()
    assert [sorted(frame["fields"]) for frame in frames] == [
        entry.names() for entry in depot.entries()
    ]


def test_revisions_and_tags_survive():
    depot = build_depot()
    restored = load(dump(depot))
    assert restored.get("e-0001").revision == 2
    assert restored.get("e-0001").tags.as_list() == ["home", "winter"]


def test_a_reloaded_depot_keeps_handing_out_fresh_ids():
    depot = build_depot()
    restored = load(dump(depot))
    assert restored.add({"title": "Sand the deck"}).id == "e-0004"


def test_archives_are_written_the_same_way_twice():
    depot = build_depot()
    assert dumps(depot) == dumps(depot)


def test_nested_values_are_carried_through():
    depot = Depot()
    depot.add({"steps": ["drain", "refill"], "meta": {"floor": 2}})
    restored = load(dump(depot))
    assert restored.get("e-0001").get("steps") == ["drain", "refill"]
    assert restored.get("e-0001").get("meta") == {"floor": 2}


def test_unwritable_values_are_refused():
    with pytest.raises(ArchiveError):
        encode_value({1: "no"})
    with pytest.raises(ArchiveError):
        encode_value(object())


def test_a_tampered_archive_is_rejected():
    payload = dump(build_depot())
    payload["entries"][0]["fields"]["title"] = "Something else"
    with pytest.raises(ArchiveError):
        load(payload)


def test_a_short_count_is_rejected():
    payload = dump(build_depot())
    payload["manifest"]["count"] = 99
    with pytest.raises(ArchiveError):
        load(payload)


def test_an_archive_from_the_future_is_rejected():
    payload = dump(build_depot())
    payload["manifest"]["version"] = 99
    with pytest.raises(ArchiveError):
        load(payload)


def test_broken_frames_are_rejected():
    with pytest.raises(ArchiveError):
        check_frame({"id": "e-0001", "revision": 1, "tags": []})
    with pytest.raises(ArchiveError):
        loads("not json at all")
    with pytest.raises(ArchiveError):
        load({"entries": "nope", "manifest": {}})


def test_manifest_helpers():
    payload = dump(build_depot())
    assert describe(payload["manifest"]) == "archive v1, 3 entry(s)"
    assert digest_of(payload["entries"]) == payload["manifest"]["digest"]
    assert json.loads(dumps(build_depot()))["manifest"] == payload["manifest"]
