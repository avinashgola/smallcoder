import pytest

from blueprint import Blueprint, Field
from blueprint.errors import BlueprintError
from cabinet import Cabinet
from paper import dump, dumps, load, loads, read_registry, summary


def build_cabinet():
    cabinet = Cabinet()
    cabinet.define(
        Blueprint(
            "task",
            [
                Field("title", "text", required=True),
                Field("minutes", "number"),
                Field("tags", "list"),
                Field("meta", "map"),
            ],
        )
    )
    cabinet.define(Blueprint("note", [Field("body", "text")]))
    cabinet.create("task", {"title": "Bleed the radiators", "tags": ["home"], "minutes": 45})
    cabinet.create("task", {"title": "Fix the gate"})
    cabinet.create("note", {"body": "Radiator key is in the drawer"})
    return cabinet


def test_round_trip_keeps_records_and_ids():
    cabinet = build_cabinet()
    restored = load(dump(cabinet))
    assert restored.items() == cabinet.items()
    assert restored.ids() == cabinet.ids()


def test_round_trip_through_text():
    cabinet = build_cabinet()
    restored = loads(dumps(cabinet))
    assert restored.all() == cabinet.all()
    assert restored.kinds() == cabinet.kinds()


def test_reloaded_blueprints_still_build_records():
    cabinet = build_cabinet()
    restored = loads(dumps(cabinet))
    fresh = restored.create("task", {"title": "Sand the deck"})
    assert fresh == "task-0003"
    assert restored.get(fresh)["tags"] == []


def test_reloaded_records_do_not_share_containers():
    cabinet = build_cabinet()
    restored = loads(dumps(cabinet))
    restored.append_to("task-0001", "tags", "winter")
    assert restored.get("task-0002")["tags"] == []


def test_reloaded_blueprints_keep_their_rules():
    cabinet = build_cabinet()
    restored = loads(dumps(cabinet))
    with pytest.raises(BlueprintError):
        restored.create("task", {"minutes": 5})


def test_saved_data_is_stable():
    cabinet = build_cabinet()
    assert dumps(cabinet) == dumps(cabinet)
    assert summary(dump(cabinet)) == "version 1, 2 blueprint(s), 3 record(s)"


def test_broken_saves_are_refused():
    payload = dump(build_cabinet())
    payload["version"] = 99
    with pytest.raises(BlueprintError):
        load(payload)
    with pytest.raises(BlueprintError):
        loads("not json")
    with pytest.raises(BlueprintError):
        load({"version": 1, "blueprints": [], "records": [{"id": "task-0001"}]})


def test_registry_can_be_read_on_its_own():
    payload = dump(build_cabinet())
    registry = read_registry(payload["blueprints"])
    assert registry.names() == ["note", "task"]
    assert registry.get("task").required_names() == ["title"]
