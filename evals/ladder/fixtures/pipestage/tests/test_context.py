import pytest

from stages.context import StageContext


def test_parameters_are_copied_not_aliased():
    params = {"region": "north"}
    ctx = StageContext("run-1", params=params)
    params["region"] = "south"
    assert ctx.param("region") == "north"
    assert ctx.param("missing", "fallback") == "fallback"


def test_require_param():
    ctx = StageContext("run-1", params={"a": 1})
    assert ctx.require_param("a") == 1
    with pytest.raises(KeyError):
        ctx.require_param("b")


def test_put_and_read_artifacts():
    ctx = StageContext("run-1")
    ctx.put_artifact("count", 3)
    assert ctx.artifact("count") == 3
    assert ctx.has_artifact("count")
    assert ctx.artifact_names() == ["count"]


def test_append_artifact_builds_a_list():
    ctx = StageContext("run-1")
    ctx.append_artifact("rejected", "a")
    ctx.append_artifact("rejected", "b")
    assert ctx.artifact("rejected") == ["a", "b"]
    assert ctx.counted("rejected") == 2
    assert ctx.counted("never-written") == 0


def test_each_run_starts_with_empty_artifacts():
    first = StageContext("run-1")
    first.append_artifact("rejected", "row-1")
    first.put_artifact("count", 1)

    second = StageContext("run-2")
    assert second.artifacts == {}
    assert second.counted("rejected") == 0


def test_a_context_given_artifacts_keeps_them_to_itself():
    shared = {"count": 1}
    ctx = StageContext("run-1", artifacts=shared)
    ctx.put_artifact("count", 99)
    assert ctx.artifact("count") == 99
    assert shared["count"] == 1


def test_with_params_copies_the_artifacts():
    ctx = StageContext("run-1", params={"a": 1})
    ctx.put_artifact("count", 1)
    child = ctx.with_params(b=2)
    assert child.params == {"a": 1, "b": 2}
    assert child.artifact("count") == 1
    child.put_artifact("count", 5)
    assert ctx.artifact("count") == 1


def test_notes_and_description():
    ctx = StageContext("run-7")
    ctx.note("hello")
    assert ctx.notes == ["hello"]
    assert ctx.describe() == "run run-7: 0 artifact(s), 1 note(s)"
    assert "run-7" in repr(ctx)
