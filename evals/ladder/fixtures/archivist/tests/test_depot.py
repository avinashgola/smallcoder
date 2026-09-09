import pytest

from depot import Depot, DepotError, Entry, EntryNotFound, FieldError
from depot.counters import Counter, is_entry_id, next_revision


def build_depot():
    depot = Depot()
    depot.add({"title": "Bleed the radiators", "minutes": 45}, tags=["home", "winter"])
    depot.add({"title": "Fix the gate", "minutes": 0}, tags=["home"])
    depot.add({"title": "File the receipts"}, tags=["admin"])
    return depot


def test_entries_come_back_in_insertion_order():
    depot = build_depot()
    assert depot.ids() == ["e-0001", "e-0002", "e-0003"]
    assert [entry.get("title") for entry in depot.entries()][0] == "Bleed the radiators"
    assert len(depot) == 3


def test_entries_handed_out_are_copies():
    depot = build_depot()
    borrowed = depot.get("e-0001")
    borrowed.fields["title"] = "changed"
    borrowed.tags.add("holiday")
    assert depot.get("e-0001").get("title") == "Bleed the radiators"
    assert depot.get("e-0001").tags.as_list() == ["home", "winter"]


def test_amend_writes_fields_and_bumps_the_revision():
    depot = build_depot()
    amended = depot.amend("e-0002", {"minutes": 15, "note": ""})
    assert amended.revision == 2
    assert amended.get("minutes") == 15
    assert amended.get("note") == ""
    assert depot.get("e-0002").get("title") == "Fix the gate"


def test_dropping_a_field_is_not_the_same_as_emptying_it():
    depot = build_depot()
    depot.amend("e-0003", {"note": ""})
    assert depot.get("e-0003").has("note")
    depot.drop_field("e-0003", "note")
    assert not depot.get("e-0003").has("note")


def test_retag_keeps_the_index_current():
    depot = build_depot()
    depot.retag("e-0002", ["admin"])
    assert [entry.id for entry in depot.by_tag("home")] == ["e-0001"]
    assert [entry.id for entry in depot.by_tag("admin")] == ["e-0002", "e-0003"]
    assert depot.tags() == ["admin", "home", "winter"]


def test_tag_and_untag():
    depot = build_depot()
    depot.tag("e-0003", "Urgent")
    assert depot.get("e-0003").tags.as_list() == ["admin", "urgent"]
    depot.untag("e-0003", "urgent")
    assert depot.get("e-0003").tags.as_list() == ["admin"]


def test_remove_forgets_the_entry_and_its_tags():
    depot = build_depot()
    depot.remove("e-0001")
    assert "e-0001" not in depot
    assert depot.by_tag("winter") == []
    with pytest.raises(EntryNotFound):
        depot.get("e-0001")


def test_by_all_tags_needs_every_tag():
    depot = build_depot()
    assert [entry.id for entry in depot.by_all_tags(["home", "winter"])] == ["e-0001"]
    assert depot.by_all_tags(["home", "admin"]) == []


def test_rebuilding_the_tag_index_changes_nothing():
    depot = build_depot()
    depot.retag("e-0001", ["admin"])
    before = depot.tag_counts()
    depot.rebuild_tag_index()
    assert depot.tag_counts() == before


def test_restore_puts_an_entry_back_untouched():
    depot = Depot()
    entry = Entry("e-0007", {"title": "Imported"}, ["home"], revision=4)
    depot.restore(entry)
    assert depot.get("e-0007") == entry
    assert depot.add({"title": "Next"}).id == "e-0008"
    with pytest.raises(DepotError):
        depot.restore(entry)


def test_bad_values_are_refused():
    depot = Depot()
    with pytest.raises(FieldError):
        depot.add({"when": {1: "no"}})
    with pytest.raises(FieldError):
        depot.add({"": 1})


def test_an_empty_change_set_is_refused():
    depot = build_depot()
    with pytest.raises(DepotError):
        depot.amend("e-0001", {})
    with pytest.raises(EntryNotFound):
        depot.amend("e-9999", {"title": "x"})


def test_counters():
    counter = Counter()
    assert counter.next_id() == "e-0001"
    assert counter.observe("e-0042")
    assert counter.next_id() == "e-0043"
    assert not counter.observe("nonsense")
    assert is_entry_id("e-0001")
    assert next_revision(1) == 2
    with pytest.raises(DepotError):
        next_revision(0)
