import pytest

from depot import Depot
from depot.errors import FieldError
from sift import (
    Every,
    FieldEquals,
    FieldMissing,
    FieldPresent,
    HasAllTags,
    HasTag,
    Some,
    TextContains,
    Unless,
    by_field,
    by_revision,
    count_matching,
    first_match,
    parse_phrase,
    partition,
    select,
)
from sift.order import newest_first
from sift.rules import RevisionAtLeast


def build_entries():
    depot = Depot()
    depot.add({"title": "Bleed the radiators", "minutes": 45}, tags=["home", "winter"])
    depot.add({"title": "Fix the gate", "minutes": 0, "done": False}, tags=["home"])
    depot.add({"title": "File the receipts", "note": ""}, tags=["admin"])
    depot.amend("e-0003", {"minutes": 20})
    return depot.entries()


def ids(entries):
    return [entry.id for entry in entries]


def test_tag_rules():
    entries = build_entries()
    assert ids(select(entries, HasTag("home"))) == ["e-0001", "e-0002"]
    assert ids(select(entries, HasAllTags(["home", "winter"]))) == ["e-0001"]
    assert ids(select(entries, Unless(HasTag("home")))) == ["e-0003"]


def test_field_rules_see_empty_values():
    entries = build_entries()
    assert ids(select(entries, FieldEquals("minutes", 0))) == ["e-0002"]
    assert ids(select(entries, FieldEquals("done", False))) == ["e-0002"]
    assert ids(select(entries, FieldEquals("note", ""))) == ["e-0003"]
    assert ids(select(entries, FieldPresent("note"))) == ["e-0003"]
    assert ids(select(entries, FieldMissing("done"))) == ["e-0001", "e-0003"]


def test_zero_is_not_false():
    entries = build_entries()
    assert select(entries, FieldEquals("minutes", False)) == []
    assert select(entries, FieldEquals("done", 0)) == []


def test_text_search():
    entries = build_entries()
    assert ids(select(entries, TextContains("title", "RADIATOR"))) == ["e-0001"]
    assert select(entries, TextContains("minutes", "45")) == []


def test_groups():
    entries = build_entries()
    both = Every([HasTag("home"), FieldEquals("minutes", 0)])
    assert ids(select(entries, both)) == ["e-0002"]
    either = Some([HasTag("admin"), FieldEquals("minutes", 45)])
    assert ids(select(entries, either)) == ["e-0001", "e-0003"]


def test_helpers():
    entries = build_entries()
    assert count_matching(entries, HasTag("home")) == 2
    assert first_match(entries, HasTag("admin")).id == "e-0003"
    assert first_match(entries, HasTag("nothing")) is None
    kept, dropped = partition(entries, HasTag("home"))
    assert (ids(kept), ids(dropped)) == (["e-0001", "e-0002"], ["e-0003"])
    with pytest.raises(TypeError):
        select(entries, "home")


def test_ordering():
    entries = build_entries()
    assert ids(by_field(entries, "minutes")) == ["e-0002", "e-0003", "e-0001"]
    assert ids(by_field(entries, "note")) == ["e-0003", "e-0001", "e-0002"]
    assert ids(by_revision(entries, descending=True))[0] == "e-0003"
    assert ids(newest_first(entries)) == ["e-0003", "e-0001", "e-0002"]
    assert select(entries, RevisionAtLeast(2))[0].id == "e-0003"


def test_phrases():
    entries = build_entries()
    assert ids(select(entries, parse_phrase("tag:home"))) == ["e-0001", "e-0002"]
    assert ids(select(entries, parse_phrase("tag:home minutes=0"))) == ["e-0002"]
    assert ids(select(entries, parse_phrase("-tag:home"))) == ["e-0003"]
    assert ids(select(entries, parse_phrase("title~gate"))) == ["e-0002"]
    assert ids(select(entries, parse_phrase("note?"))) == ["e-0003"]
    assert ids(select(entries, parse_phrase("done!"))) == ["e-0001", "e-0003"]
    assert ids(select(entries, parse_phrase("done=false"))) == ["e-0002"]


def test_bad_phrases():
    with pytest.raises(FieldError):
        parse_phrase("   ")
    with pytest.raises(FieldError):
        parse_phrase("just-a-word")
