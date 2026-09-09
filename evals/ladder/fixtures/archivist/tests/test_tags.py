import pytest

from depot.errors import TagError
from depot.tags import TagIndex, TagSet, normalize_tag


def test_tags_are_normalised():
    assert normalize_tag("  Home ") == "home"
    with pytest.raises(TagError):
        normalize_tag("")
    with pytest.raises(TagError):
        normalize_tag("two words")
    with pytest.raises(TagError):
        normalize_tag("x" * 40)


def test_tag_sets_are_sorted_and_unique():
    tags = TagSet(["Winter", "home", "winter"])
    assert tags.as_list() == ["home", "winter"]
    assert len(tags) == 2
    assert tags.holds("HOME")
    assert not tags.holds("admin")


def test_tag_sets_compare_against_plain_lists():
    assert TagSet(["home"]) == ["Home"]
    assert TagSet(["home", "winter"]) == TagSet(["winter", "home"])


def test_add_and_discard():
    tags = TagSet(["home"])
    tags.add("Winter").discard("home")
    assert tags.as_list() == ["winter"]
    assert tags.holds_any(["winter", "admin"])
    assert not tags.holds_all(["winter", "admin"])


def test_copies_are_independent():
    tags = TagSet(["home"])
    copy = tags.copy()
    copy.add("winter")
    assert tags.as_list() == ["home"]


def test_index_groups_ids_by_tag():
    index = TagIndex()
    index.add("e-0001", ["home", "winter"])
    index.add("e-0002", ["home"])
    assert index.ids_for("home") == ["e-0001", "e-0002"]
    assert index.ids_for_all(["home", "winter"]) == ["e-0001"]
    assert index.ids_for_any(["winter", "admin"]) == ["e-0001"]
    assert index.counts() == {"home": 2, "winter": 1}


def test_index_forgets_empty_tags():
    index = TagIndex()
    index.add("e-0001", ["home"])
    index.remove("e-0001", ["home"])
    assert index.tags() == []
    assert len(index) == 0


def test_index_replace_moves_an_entry():
    index = TagIndex()
    index.add("e-0001", ["home"])
    index.replace("e-0001", ["home"], ["admin"])
    assert index.ids_for("home") == []
    assert index.ids_for("admin") == ["e-0001"]
