import pytest

from blueprint import Field
from blueprint.defaults import blank_for, clone_default, kind_of
from blueprint.errors import FieldError, ValidationError


def test_names_are_canonical():
    assert Field(" Title ").name == "title"
    with pytest.raises(FieldError):
        Field("")
    with pytest.raises(FieldError):
        Field("two words")
    with pytest.raises(FieldError):
        Field(7)


def test_defaults_follow_the_type():
    assert Field("title", "text").default == ""
    assert Field("minutes", "number").default == 0
    assert Field("done", "flag").default is False
    assert Field("tags", "list").default == []
    assert Field("meta", "map").default == {}


def test_blank_hands_out_a_fresh_container():
    field = Field("tags", "list")
    first = field.blank()
    first.append("home")
    assert field.blank() == []
    assert field.default == []


def test_an_explicit_default_is_checked():
    assert Field("minutes", "number", default=30).default == 30
    with pytest.raises(ValidationError):
        Field("minutes", "number", default="soon")


def test_casting_is_narrow():
    number = Field("minutes", "number")
    assert number.cast("30") == 30
    assert number.cast("1.5") == 1.5
    with pytest.raises(ValidationError):
        number.cast(True)
    assert Field("title").cast(7) == "7"
    assert Field("tags", "list").cast(("a", "b")) == ["a", "b"]


def test_checking_rejects_the_wrong_type():
    with pytest.raises(ValidationError):
        Field("tags", "list").check("home")
    with pytest.raises(ValidationError):
        Field("done", "flag").check(1)


def test_required_fields_reject_blanks():
    field = Field("title", required=True)
    with pytest.raises(ValidationError):
        field.check(None)
    with pytest.raises(ValidationError):
        field.check("")
    assert field.check("Fix the gate") == "Fix the gate"


def test_choices():
    field = Field("status", "text", choices=["open", "done"])
    assert field.accept("open") == "open"
    with pytest.raises(ValidationError):
        field.accept("halfway")
    with pytest.raises(FieldError):
        Field("tags", "list", choices=[[]])


def test_describe_round_trip():
    field = Field("status", "text", required=True, default="open", choices=["open", "done"])
    assert Field.from_description(field.describe()) == field
    assert field.describe()["default"] == "open"


def test_described_defaults_are_copies():
    field = Field("tags", "list")
    described = field.describe()
    described["default"].append("home")
    assert field.default == []


def test_value_helpers():
    assert kind_of(True) == "flag"
    assert kind_of(2.5) == "number"
    assert kind_of(None) is None
    assert blank_for("map") == {}
    nested = [{"a": [1]}]
    assert clone_default(nested) == nested
    assert clone_default(nested)[0]["a"] is not nested[0]["a"]
    with pytest.raises(FieldError):
        blank_for("date")
