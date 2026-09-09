"""The stages that ship with the project, and a registry holding them."""

from stages.builtin.aggregate import CountStage, GroupSumStage
from stages.builtin.filterby import FilterStage, RequireFieldsStage
from stages.builtin.sink import CollectStage
from stages.builtin.transform import DeriveStage, MapStage, RenameStage
from stages.registry import StageRegistry

DEFAULT_REGISTRY = StageRegistry(
    {
        "map": MapStage,
        "rename": RenameStage,
        "derive": DeriveStage,
        "filter": FilterStage,
        "require": RequireFieldsStage,
        "group_sum": GroupSumStage,
        "count": CountStage,
        "collect": CollectStage,
    }
)

__all__ = [
    "CollectStage",
    "CountStage",
    "DEFAULT_REGISTRY",
    "DeriveStage",
    "FilterStage",
    "GroupSumStage",
    "MapStage",
    "RenameStage",
    "RequireFieldsStage",
]
