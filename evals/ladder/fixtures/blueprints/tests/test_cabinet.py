import pytest

from blueprint import Blueprint, Field
from blueprint.errors import RecordNotFound, UnknownField, ValidationError
from cabinet import Cabinet


def task_blueprint():
    return Blueprint(
        "task",
        [
            Field("title", "text", required=True),
            Field("minutes", "number"),
            Field("tags", "list"),
            Field("meta", "map"),
            Field("done", "flag"),
        ],
    )


def note_blueprint():
    return Blueprint("note", [Field("body", "text"), Field("pinned", "flag")])


def build_cabinet():
    cabinet = Cabinet()
    cabinet.define(task_blueprint())
    cabinet.define(note_blueprint())
    return cabinet


def test_a_new_record_carries_every_declared_field():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    assert cabinet.get(task) == {
        "title": "Bleed the radiators",
        "minutes": 0,
        "tags": [],
        "meta": {},
        "done": False,
    }


def test_ids_run_per_kind():
    cabinet = build_cabinet()
    assert cabinet.create("task", {"title": "Bleed the radiators"}) == "task-0001"
    assert cabinet.create("note", {"body": "hello"}) == "note-0001"
    assert cabinet.create("task", {"title": "Fix the gate"}) == "task-0002"
    assert cabinet.ids("task") == ["task-0001", "task-0002"]
    assert cabinet.count() == 3


def test_records_handed_out_are_copies():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    borrowed = cabinet.get(task)
    borrowed["tags"].append("home")
    borrowed["title"] = "changed"
    assert cabinet.get(task)["tags"] == []
    assert cabinet.get(task)["title"] == "Bleed the radiators"


def test_two_records_do_not_share_a_list():
    cabinet = build_cabinet()
    first = cabinet.create("task", {"title": "Bleed the radiators"})
    second = cabinet.create("task", {"title": "Fix the gate"})
    cabinet.append_to(first, "tags", "home")
    assert cabinet.get(first)["tags"] == ["home"]
    assert cabinet.get(second)["tags"] == []


def test_a_later_record_still_starts_empty():
    cabinet = build_cabinet()
    first = cabinet.create("task", {"title": "Bleed the radiators"})
    cabinet.append_to(first, "tags", "home")
    later = cabinet.create("task", {"title": "Sand the deck"})
    assert cabinet.get(later)["tags"] == []


def test_two_records_do_not_share_a_map():
    cabinet = build_cabinet()
    first = cabinet.create("task", {"title": "Bleed the radiators"})
    second = cabinet.create("task", {"title": "Fix the gate"})
    cabinet.put_in(first, "meta", "floor", 2)
    assert cabinet.get(first)["meta"] == {"floor": 2}
    assert cabinet.get(second)["meta"] == {}


def test_a_supplied_list_is_kept_apart_from_the_caller():
    cabinet = build_cabinet()
    tags = ["home"]
    task = cabinet.create("task", {"title": "Bleed the radiators", "tags": tags})
    cabinet.append_to(task, "tags", "winter")
    assert tags == ["home"]


def test_update_writes_only_the_named_fields():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    updated = cabinet.update(task, {"minutes": "45"})
    assert updated["minutes"] == 45
    assert updated["title"] == "Bleed the radiators"
    with pytest.raises(ValidationError):
        cabinet.update(task, {})
    with pytest.raises(ValidationError):
        cabinet.update(task, {"title": ""})


def test_list_and_map_operations():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    cabinet.extend_with(task, "tags", ["home", "winter"])
    cabinet.remove_from(task, "tags", "home")
    assert cabinet.get(task)["tags"] == ["winter"]
    cabinet.put_in(task, "meta", "floor", 2)
    assert cabinet.value_of(task, "meta") == {"floor": 2}
    with pytest.raises(ValidationError):
        cabinet.append_to(task, "title", "no")
    with pytest.raises(ValidationError):
        cabinet.put_in(task, "meta", 7, "no")


def test_number_and_flag_operations():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    cabinet.increment(task, "minutes", 15)
    cabinet.increment(task, "minutes")
    assert cabinet.get(task)["minutes"] == 16
    assert cabinet.toggle(task, "done")["done"] is True
    with pytest.raises(ValidationError):
        cabinet.increment(task, "title")


def test_resetting_a_field_gives_a_fresh_container():
    cabinet = build_cabinet()
    first = cabinet.create("task", {"title": "Bleed the radiators", "tags": ["home"]})
    second = cabinet.create("task", {"title": "Fix the gate", "tags": ["home"]})
    cabinet.reset_field(first, "tags")
    cabinet.append_to(second, "tags", "winter")
    assert cabinet.get(first)["tags"] == []
    assert cabinet.get(second)["tags"] == ["home", "winter"]


def test_rows_carry_the_id_and_kind():
    cabinet = build_cabinet()
    cabinet.create("task", {"title": "Bleed the radiators"})
    cabinet.create("note", {"body": "hello"})
    rows = cabinet.rows(fields=["title", "body"])
    assert rows[0]["id"] == "task-0001"
    assert rows[0]["kind"] == "task"
    assert rows[1]["body"] == "hello"


def test_delete_forgets_the_record_but_not_the_number():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    cabinet.delete(task)
    assert task not in cabinet
    assert cabinet.create("task", {"title": "Fix the gate"}) == "task-0002"
    with pytest.raises(RecordNotFound):
        cabinet.get(task)


def test_restore_puts_a_record_back_under_its_id():
    cabinet = build_cabinet()
    cabinet.restore("task-0009", "task", {"title": "Imported"})
    assert cabinet.get("task-0009")["tags"] == []
    assert cabinet.create("task", {"title": "Next"}) == "task-0010"
    with pytest.raises(ValidationError):
        cabinet.restore("task-0009", "task", {"title": "Again"})


def test_unknown_fields_and_records_are_refused():
    cabinet = build_cabinet()
    task = cabinet.create("task", {"title": "Bleed the radiators"})
    with pytest.raises(UnknownField):
        cabinet.update(task, {"colour": "red"})
    with pytest.raises(UnknownField):
        cabinet.field_of(task, "colour")
    with pytest.raises(RecordNotFound):
        cabinet.kind_of("task-9999")
