import pytest

from common.errors import ConfigError, StageError
from common.records import Record, records_from
from stages.base import RecordStage, Stage
from stages.context import StageContext
from stages.registry import StageRegistry
from stages.result import StageResult


class Doubler(RecordStage):
    kind = "doubler"

    def handle(self, record, ctx):
        return record.with_field("n", record.get("n", 0) * 2)


class DropOdd(RecordStage):
    kind = "drop-odd"

    def handle(self, record, ctx):
        return None if record.get("n", 0) % 2 else record


class Explodes(Stage):
    def process(self, records, ctx):
        raise ValueError("kaboom")


def test_stage_names_are_slugified():
    assert Doubler("Double The Rows").name == "double-the-rows"
    with pytest.raises(ConfigError):
        Doubler("   ")


def test_run_returns_counts():
    ctx = StageContext("run-1")
    result = Doubler("double").run(records_from([{"n": 1}, {"n": 2}]), ctx)
    assert result.count_in == 2
    assert result.count_out == 2
    assert result.dropped == 0
    assert [r.get("n") for r in result.records] == [2, 4]


def test_dropping_records_is_counted():
    ctx = StageContext("run-1")
    result = DropOdd("evens").run(records_from([{"n": 1}, {"n": 2}]), ctx)
    assert result.count_in == 2
    assert result.count_out == 1
    assert result.dropped == 1
    assert result.kept_percent == 50.0


def test_unexpected_errors_are_wrapped_with_the_stage_name():
    with pytest.raises(StageError) as info:
        Explodes("boom").run([], StageContext("run-1"))
    assert "boom" in str(info.value)
    assert "kaboom" in str(info.value)


def test_base_stage_must_be_subclassed():
    with pytest.raises(StageError):
        Stage("plain").run([Record({})], StageContext("run-1"))


def test_result_helpers():
    result = StageResult("s", [Record({})], 4, stats={"op": "eq"})
    assert result.as_row() == ("s", 4, 1, 3)
    assert result.stat("op") == "eq"
    assert result.stat("missing", 0) == 0
    assert "1 out" in result.describe()


def test_registry_creates_stages_from_config():
    registry = StageRegistry({"doubler": Doubler})
    stage = registry.create({"type": "doubler", "name": "Double"})
    assert isinstance(stage, Doubler)
    assert stage.name == "double"
    assert registry.kinds() == ["doubler"]


def test_registry_reports_unknown_types():
    registry = StageRegistry({"doubler": Doubler})
    with pytest.raises(ConfigError):
        registry.create({"type": "nope", "name": "x"})
    with pytest.raises(ConfigError):
        registry.create({"name": "x"})


def test_registry_reports_bad_options():
    registry = StageRegistry({"doubler": Doubler})
    with pytest.raises(ConfigError):
        registry.create({"type": "doubler", "name": "x", "colour": "blue"})


def test_registries_merge():
    left = StageRegistry({"doubler": Doubler})
    right = StageRegistry({"drop": DropOdd})
    assert left.merged(right).kinds() == ["doubler", "drop"]
