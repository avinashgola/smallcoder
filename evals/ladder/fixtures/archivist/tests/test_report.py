import pytest

from depot import Depot, Entry, format_entry, summarize
from depot.report import field_usage, format_value, render_lines


def build_depot():
    depot = Depot()
    depot.add({"title": "Bleed the radiators", "minutes": 45}, tags=["home", "winter"])
    depot.add({"title": "Fix the gate", "minutes": 0, "done": False}, tags=["home"])
    depot.add({"title": "File the receipts", "note": ""})
    depot.amend("e-0001", {"minutes": 50})
    return depot


def test_empty_values_are_shown_not_hidden():
    assert format_value(0) == "0"
    assert format_value(False) == "no"
    assert format_value("") == '""'
    assert format_value(None) == "-"


def test_containers_are_rendered_in_a_stable_order():
    assert format_value(["b", "a"]) == "[b, a]"
    assert format_value({"b": 1, "a": 2}) == "{a: 2, b: 1}"


def test_one_entry_reads_as_a_line():
    entry = Entry("e-0002", {"title": "Fix the gate", "minutes": 0}, ["home"], revision=1)
    assert format_entry(entry) == "e-0002 r1 [home] minutes=0 title=Fix the gate"


def test_an_untagged_entry_shows_a_dash():
    entry = Entry("e-0003", {"title": "File the receipts"})
    assert format_entry(entry) == "e-0003 r1 [-] title=File the receipts"


def test_named_fields_only():
    entry = Entry("e-0002", {"title": "Fix the gate", "minutes": 0}, ["home"])
    assert format_entry(entry, ["minutes"]) == "e-0002 r1 [home] minutes=0"


def test_lines_for_a_whole_depot():
    lines = render_lines(build_depot().entries(), ["title"])
    assert lines[0] == "e-0001 r2 [home,winter] title=Bleed the radiators"
    assert len(lines) == 3


def test_field_usage_counts_entries_not_values():
    usage = field_usage(build_depot().entries())
    assert usage == {"title": 3, "minutes": 2, "done": 1, "note": 1}


def test_summary():
    assert summarize(build_depot()) == {
        "entries": 3,
        "tags": 2,
        "fields": 4,
        "amended": 1,
    }


def test_only_entries_can_be_formatted():
    with pytest.raises(TypeError):
        format_entry({"id": "e-0001"})
