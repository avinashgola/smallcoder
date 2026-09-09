import pytest

from common.errors import ConfigError
from pipeline.build import build_from_stages, build_pipeline
from pipeline.plan import Plan
from stages.builtin import DEFAULT_REGISTRY
from stages.builtin.transform import MapStage

STAGES = [
    {"type": "map", "name": "Lower Region", "field": "region", "using": "lower"},
    {"type": "count", "name": "size", "into": "rows"},
]


def test_plan_names_are_slugified():
    plan = Plan("Orders Report", STAGES)
    assert plan.name == "orders-report"
    assert plan.stage_names() == ["lower-region", "size"]
    assert plan.types_used() == ["count", "map"]
    assert len(plan) == 2


def test_plan_needs_stages():
    with pytest.raises(ConfigError):
        Plan("empty", [])


def test_plan_validation_catches_duplicates():
    stages = STAGES + [{"type": "count", "name": "size", "into": "again"}]
    with pytest.raises(ConfigError):
        Plan("dupes", stages).validate()


def test_plan_validation_catches_unknown_types():
    stages = [{"type": "teleport", "name": "x"}]
    with pytest.raises(ConfigError):
        Plan("odd", stages).validate(DEFAULT_REGISTRY)


def test_plan_validation_needs_name_and_type():
    with pytest.raises(ConfigError):
        Plan("odd", [{"type": "count"}]).validate()


def test_plans_can_be_edited_without_mutation():
    plan = Plan("orders", STAGES)
    bigger = plan.with_stage({"type": "count", "name": "extra"})
    assert len(plan) == 2
    assert len(bigger) == 3
    smaller = bigger.without_stage("extra")
    assert smaller.stage_names() == ["lower-region", "size"]
    with pytest.raises(ConfigError):
        plan.without_stage("nope")


def test_plan_from_dict():
    plan = Plan.from_dict({"name": "orders", "stages": STAGES, "params": {"a": 1}})
    assert plan.params == {"a": 1}
    assert "lower-region -> size" in plan.describe()


def test_build_pipeline_instantiates_the_stages():
    pipeline = build_pipeline({"name": "orders", "stages": STAGES})
    assert pipeline.stage_names() == ["lower-region", "size"]
    assert pipeline.stage("size").into == "rows"
    with pytest.raises(KeyError):
        pipeline.stage("missing")


def test_build_from_stages():
    pipeline = build_from_stages("manual", [MapStage("m", field="region")])
    assert len(pipeline) == 1
    assert pipeline.describe() == "manual: m"
