import pytest

from common.errors import ConfigError
from common.records import records_from, to_dicts
from stages.builtin import DEFAULT_REGISTRY
from stages.builtin.aggregate import CountStage, GroupSumStage
from stages.builtin.filterby import FilterStage, RequireFieldsStage
from stages.builtin.sink import CollectStage
from stages.builtin.transform import DeriveStage, MapStage, RenameStage
from stages.context import StageContext

ROWS = records_from(
    [
        {"region": "North", "amount": "10"},
        {"region": "north", "amount": "5"},
        {"region": "South", "amount": "-2"},
    ]
)


def ctx():
    return StageContext("run-1")


def test_map_applies_the_named_transform():
    result = MapStage("lower", field="region", using="lower").run(ROWS, ctx())
    assert [r.get("region") for r in result.records] == ["north", "north", "south"]


def test_map_rejects_an_unknown_transform():
    with pytest.raises(ConfigError):
        MapStage("bad", field="region", using="explode")


def test_rename_moves_fields():
    result = RenameStage("rename", mapping={"amount": "value"}).run(ROWS, ctx())
    assert "value" in result.records[0]
    assert "amount" not in result.records[0]


def test_derive_computes_a_new_field():
    rows = records_from([{"a": "2", "b": "3"}])
    result = DeriveStage("total", target="sum", sources=["a", "b"]).run(rows, ctx())
    assert result.records[0].get("sum") == 5.0


def test_filter_keeps_matching_records_and_records_rejects():
    scratch = ctx()
    stage = FilterStage("positive", field="amount", op="gt", value=0)
    result = stage.run(ROWS, scratch)
    assert result.count_out == 2
    assert scratch.counted("rejected") == 1
    assert scratch.artifact("reject_reasons")[0].startswith("positive:")


def test_filter_drops_records_without_the_field():
    scratch = ctx()
    rows = records_from([{"other": 1}])
    assert FilterStage("f", field="amount", op="gt", value=0).run(rows, scratch).count_out == 0
    assert FilterStage("f", field="amount", op="gt", value=0, keep_missing=True).run(
        rows, scratch
    ).count_out == 1


def test_require_fields_drops_incomplete_records():
    scratch = ctx()
    rows = records_from([{"region": "n", "amount": 1}, {"region": "n"}])
    result = RequireFieldsStage("have", fields=["region", "amount"]).run(rows, scratch)
    assert result.count_out == 1
    assert scratch.counted("rejected") == 1


def test_group_sum_collapses_records():
    scratch = ctx()
    rows = records_from(
        [
            {"region": "north", "amount": "10"},
            {"region": "south", "amount": "4"},
            {"region": "north", "amount": "5"},
        ]
    )
    stage = GroupSumStage("by-region", group_by="region", value_field="amount",
                          into="total")
    result = stage.run(rows, scratch)
    assert to_dicts(result.records) == [
        {"region": "north", "total": 15.0},
        {"region": "south", "total": 4.0},
    ]
    assert scratch.artifact("by-region_groups") == 2


def test_count_stage_passes_records_through():
    scratch = ctx()
    result = CountStage("size", into="row_count").run(ROWS, scratch)
    assert result.count_out == 3
    assert scratch.artifact("row_count") == 3


def test_collect_stores_the_batch():
    scratch = ctx()
    result = CollectStage("out", into="rows").run(ROWS, scratch)
    assert result.count_out == 3
    assert scratch.artifact("rows") == to_dicts(ROWS)
    assert scratch.notes == ["out collected 3 record(s)"]


def test_default_registry_knows_every_builtin():
    assert DEFAULT_REGISTRY.kinds() == [
        "collect",
        "count",
        "derive",
        "filter",
        "group_sum",
        "map",
        "rename",
        "require",
    ]
