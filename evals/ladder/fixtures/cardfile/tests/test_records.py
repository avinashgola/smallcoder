import pytest

from catalog.changes import DELETE, apply_changes, is_noop, normalize_changes, touched_fields
from catalog.errors import SchemaError
from catalog.ids import IdAllocator, is_valid_id, parse_id, sort_key
from catalog.records import diff, field_names, merge, normalize_record, pluck, project


def test_field_names_are_canonicalised():
    assert normalize_record({" Title ": "Fix the gate"}) == {"title": "Fix the gate"}
    with pytest.raises(SchemaError):
        normalize_record({"": 1})
    with pytest.raises(SchemaError):
        normalize_record({"id": "rec-0001"})


def test_normalize_record_copies_containers():
    tags = ["outdoor"]
    record = normalize_record({"tags": tags})
    tags.append("indoor")
    assert record["tags"] == ["outdoor"]


def test_project_and_merge():
    record = {"title": "Fix the gate", "status": "open", "score": 10}
    assert project(record, ["title", "missing"]) == {"title": "Fix the gate"}
    assert merge(record, {"status": "done"})["status"] == "done"
    assert record["status"] == "open"


def test_diff_reports_both_sides():
    before = {"status": "open", "owner": "ana"}
    after = {"status": "done", "owner": "ana"}
    assert diff(before, after) == {"status": ("open", "done")}


def test_field_names_and_pluck():
    rows = [{"a": 1}, {"b": 2}]
    assert field_names(rows) == ["a", "b"]
    assert pluck(rows, "a", default=0) == [1, 0]


def test_change_sets_are_validated():
    assert normalize_changes({"Status": "done"}) == {"status": "done"}
    assert touched_fields({"Status": "done", "owner": "ana"}) == ["owner", "status"]
    with pytest.raises(SchemaError):
        normalize_changes({})
    with pytest.raises(SchemaError):
        normalize_changes({"status": DELETE})


def test_noop_detection_and_application():
    record = {"status": "open", "owner": "ana"}
    assert is_noop(record, {"status": "open"})
    assert not is_noop(record, {"status": "done"})
    assert apply_changes(record, {"status": "done"}) == {"status": "done", "owner": "ana"}
    assert record["status"] == "open"


def test_ids_are_sequential_and_padded():
    allocator = IdAllocator("job", width=3)
    assert [allocator.next_id() for _ in range(3)] == ["job-001", "job-002", "job-003"]
    assert allocator.issued == 3


def test_reserving_pushes_the_counter_past_an_import():
    allocator = IdAllocator()
    assert allocator.reserve("rec-0042")
    assert allocator.next_id() == "rec-0043"
    assert not allocator.reserve("other-0001")
    assert not allocator.reserve("not an id")


def test_id_parsing_and_sorting():
    assert parse_id("rec-0007") == ("rec", 7)
    assert is_valid_id("rec-0007")
    assert not is_valid_id("Rec-7x")
    assert sorted(["rec-0010", "rec-0002", "loose"], key=sort_key) == [
        "loose",
        "rec-0002",
        "rec-0010",
    ]


def test_bad_prefixes_are_refused():
    with pytest.raises(SchemaError):
        IdAllocator("1bad")
    with pytest.raises(SchemaError):
        IdAllocator("re c")
