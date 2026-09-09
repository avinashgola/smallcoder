import pytest

from blueprint import Blueprint, Field, Registry
from blueprint.errors import BlueprintError, FieldError, UnknownField, ValidationError


def task_blueprint():
    return Blueprint(
        "task",
        [
            Field("title", "text", required=True),
            Field("minutes", "number"),
            Field("tags", "list"),
            Field("done", "flag"),
        ],
    )


def test_a_blueprint_lists_its_fields_in_order():
    blueprint = task_blueprint()
    assert blueprint.names() == ["title", "minutes", "tags", "done"]
    assert blueprint.required_names() == ["title"]
    assert [field.name for field in blueprint.containers()] == ["tags"]
    assert len(blueprint) == 4


def test_fields_are_looked_up_by_canonical_name():
    blueprint = task_blueprint()
    assert blueprint.field(" Title ").kind == "text"
    assert blueprint.has("minutes")
    with pytest.raises(UnknownField):
        blueprint.field("colour")


def test_duplicate_and_empty_declarations_are_refused():
    with pytest.raises(FieldError):
        Blueprint("task", [Field("title"), Field("title")])
    with pytest.raises(BlueprintError):
        Blueprint("task", [])
    with pytest.raises(FieldError):
        Blueprint("task", ["title"])


def test_accept_casts_and_checks():
    blueprint = task_blueprint()
    assert blueprint.accept({"minutes": "30"}) == {"minutes": 30}
    with pytest.raises(UnknownField):
        blueprint.accept({"colour": "red"})
    with pytest.raises(ValidationError):
        blueprint.accept({"tags": "home"})


def test_check_complete_looks_at_required_fields():
    blueprint = task_blueprint()
    with pytest.raises(ValidationError):
        blueprint.check_complete({"title": "", "minutes": 0})
    assert blueprint.check_complete({"title": "Fix the gate"})


def test_describe_round_trip():
    blueprint = task_blueprint()
    rebuilt = Blueprint.from_description(blueprint.describe())
    assert rebuilt.names() == blueprint.names()
    assert rebuilt.field("title").required


def test_registry_holds_one_blueprint_per_name():
    registry = Registry([task_blueprint()])
    assert registry.names() == ["task"]
    assert registry.has("task")
    with pytest.raises(BlueprintError):
        registry.register(task_blueprint())
    with pytest.raises(BlueprintError):
        registry.get("note")
    assert len(registry) == 1
