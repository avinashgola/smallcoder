import pytest

from common.errors import ConfigError, MissingField
from common.numbers import as_number, clamp, mean, percent, round_to, safe_div
from common.records import Record, field_values, records_from, to_dicts
from common.strings import pad, slugify, snake_case, title_case, truncate
from common.validators import (
    non_empty_string,
    one_of,
    positive_int,
    reject_keys,
    require_keys,
)


def test_record_reading():
    record = Record({"a": 1, "b": 2})
    assert record["a"] == 1
    assert record.get("missing", "default") == "default"
    assert "b" in record
    assert len(record) == 2
    assert record.as_dict() == {"a": 1, "b": 2}


def test_record_require_reports_the_stage():
    with pytest.raises(MissingField):
        Record({}).require("amount", stage="totals")


def test_records_are_immutable_under_derivation():
    record = Record({"a": 1})
    derived = record.with_field("b", 2)
    assert record.as_dict() == {"a": 1}
    assert derived.as_dict() == {"a": 1, "b": 2}
    assert derived.without("a") == {"b": 2}
    assert record.renamed({"a": "z"}) == {"z": 1}


def test_record_helpers():
    rows = records_from([{"a": 1}, Record({"a": 2})])
    assert to_dicts(rows) == [{"a": 1}, {"a": 2}]
    assert field_values(rows, "a") == [1, 2]


def test_numbers():
    assert safe_div(1, 0) == 0.0
    assert safe_div(3, 2) == 1.5
    assert round_to(1.2345) == 1.23
    assert clamp(5, 1, 3) == 3
    assert mean([1, 2, 3]) == 2.0
    assert mean([]) == 0.0
    assert percent(1, 4) == 25.0


def test_as_number_is_forgiving():
    assert as_number("12.5") == 12.5
    assert as_number(" 7 ") == 7.0
    assert as_number("nope") == 0.0
    assert as_number(True) == 0.0


def test_strings():
    assert slugify("  Total Amount! ") == "total-amount"
    assert snake_case("Total Amount") == "total_amount"
    assert title_case("total-amount") == "Total Amount"
    assert truncate("abcdefgh", 5) == "ab..."
    assert pad("ab", 4) == "ab  "


def test_validators():
    require_keys({"a": 1}, ["a"])
    with pytest.raises(ConfigError):
        require_keys({}, ["a"])
    with pytest.raises(ConfigError):
        reject_keys({"z": 1}, ["a"])
    assert positive_int(2, "n") == 2
    with pytest.raises(ConfigError):
        positive_int(0, "n")
    assert one_of("a", ["a", "b"], "choice") == "a"
    with pytest.raises(ConfigError):
        one_of("c", ["a", "b"], "choice")
    assert non_empty_string("  x ", "name") == "x"
    with pytest.raises(ConfigError):
        non_empty_string("  ", "name")
