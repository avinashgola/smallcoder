import pytest

from envcfg.errors import CastError, InvalidSetting, MissingSetting
from envcfg.loader import load, load_many
from envcfg.spec import Field, Spec

WORKER_SPEC = Spec(
    "WORKER_",
    (
        Field("queue", default="default"),
        Field("concurrency", kind="int", default=2),
        Field("verbose", kind="bool", default=False),
    ),
)

REPORT_SPEC = Spec(
    "REPORT_",
    (
        Field("format", default="json", choices=("json", "csv")),
        Field("rows", kind="int", default=100),
    ),
)


def test_values_come_from_the_environment():
    values = load({"WORKER_QUEUE": "urgent", "WORKER_CONCURRENCY": "8"}, WORKER_SPEC)
    assert values["queue"] == "urgent"
    assert values["concurrency"] == 8


def test_unset_variables_fall_back_to_declared_defaults():
    values = load({}, WORKER_SPEC)
    assert values == {"queue": "default", "concurrency": 2, "verbose": False}


def test_blank_variable_counts_as_unset():
    assert load({"WORKER_QUEUE": "   "}, WORKER_SPEC)["queue"] == "default"


def test_overrides_beat_the_environment():
    values = load({"WORKER_QUEUE": "urgent"}, WORKER_SPEC, {"queue": "slow"})
    assert values["queue"] == "slow"


def test_required_variable_is_reported_by_name():
    spec = Spec("WORKER_", (Field("token", required=True),))
    with pytest.raises(MissingSetting) as info:
        load({}, spec)
    assert info.value.variable == "WORKER_TOKEN"


def test_bad_value_names_the_variable_it_came_from():
    with pytest.raises(CastError) as info:
        load({"WORKER_CONCURRENCY": "many"}, WORKER_SPEC)
    assert info.value.where == "WORKER_CONCURRENCY"


def test_choices_are_enforced():
    with pytest.raises(InvalidSetting):
        load({"REPORT_FORMAT": "pdf"}, REPORT_SPEC)


def test_load_many_keys_results_by_prefix():
    loaded = load_many({"REPORT_ROWS": "5"}, [WORKER_SPEC, REPORT_SPEC])
    assert loaded["REPORT_"]["rows"] == 5
    assert loaded["WORKER_"]["concurrency"] == 2


def test_one_load_does_not_inherit_the_previous_one():
    first = load({"WORKER_CONCURRENCY": "16"}, WORKER_SPEC)
    second = load({}, WORKER_SPEC)
    assert first["concurrency"] == 16
    assert second["concurrency"] == 2


def test_callers_override_mapping_is_left_alone():
    overrides = {"queue": "urgent"}
    values = load({}, WORKER_SPEC, overrides)
    assert values["queue"] == "urgent"
    assert overrides == {"queue": "urgent"}


def test_result_holds_exactly_the_fields_of_its_own_spec():
    load({"REPORT_FORMAT": "csv"}, REPORT_SPEC)
    values = load({}, WORKER_SPEC)
    assert sorted(values) == ["concurrency", "queue", "verbose"]
