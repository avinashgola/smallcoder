"""Building the runnable pipeline out of a plan."""

from stages.builtin import DEFAULT_REGISTRY
from pipeline.plan import Plan
from pipeline.run import Pipeline


def build_pipeline(plan, registry=None):
    """Validate `plan` and instantiate every stage it names."""
    registry = registry or DEFAULT_REGISTRY
    if isinstance(plan, dict):
        plan = Plan.from_dict(plan)
    plan.validate(registry)
    stages = registry.create_all(plan.stages)
    return Pipeline(plan.name, stages, params=plan.params)


def build_from_stages(name, stages, params=None):
    """Build a pipeline from already constructed stage objects."""
    return Pipeline(name, list(stages), params=params)
