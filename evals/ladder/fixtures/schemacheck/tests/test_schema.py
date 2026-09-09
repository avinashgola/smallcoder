import pytest

from schemacheck.errors import ValidationError
from schemacheck.fields import Field
from schemacheck.schema import Schema

CONTACT = Schema(
    "contact",
    (
        Field("first_name", min_length=2, max_length=20),
        Field("email", email=True),
        Field("age", kind="int", required=False, minimum=18, maximum=99),
    ),
)

GOOD = {"first_name": "Ada", "email": "ada@example.com", "age": 36}


def test_a_matching_payload_has_no_errors():
    assert CONTACT.errors_for(GOOD) == []
    assert CONTACT.is_valid(GOOD) is True


def test_an_optional_field_may_be_left_out():
    assert CONTACT.errors_for({"first_name": "Ada", "email": "ada@example.com"}) == []


def test_missing_required_fields_are_listed():
    assert CONTACT.errors_for({}) == [
        "first_name: this field is required",
        "email: this field is required",
    ]


def test_a_bad_value_is_described():
    payload = dict(GOOD, first_name="A")
    assert CONTACT.errors_for(payload) == ["first_name: must be at least 2 characters"]


def test_a_blank_string_is_not_acceptable():
    payload = dict(GOOD, first_name="   ")
    assert CONTACT.errors_for(payload) == ["first_name: must not be blank"]


def test_problems_after_a_good_field_are_still_found():
    payload = {"first_name": "Ada", "email": "nope", "age": 150}
    assert CONTACT.errors_for(payload) == [
        "email: must look like an email address",
        "age: must be 99 or less",
    ]


def test_wrong_types_are_reported():
    payload = {"first_name": 5, "email": "ada@example.com", "age": "36"}
    assert CONTACT.errors_for(payload) == [
        "first_name: must be a str",
        "age: must be a int",
    ]


def test_fields_the_schema_does_not_declare_are_reported():
    payload = dict(GOOD, nickname="the countess")
    assert CONTACT.errors_for(payload) == ["nickname: unknown field"]


def test_is_valid_agrees_with_the_error_list():
    payload = dict(GOOD, age=150)
    assert CONTACT.is_valid(payload) is False


def test_validate_raises_carrying_every_message():
    payload = {"first_name": "Ada", "email": "nope", "age": 10}
    with pytest.raises(ValidationError) as info:
        CONTACT.validate(payload)
    assert info.value.errors == (
        "email: must look like an email address",
        "age: must be 18 or more",
    )


def test_validate_returns_the_payload_it_was_given():
    assert CONTACT.validate(GOOD) is GOOD


def test_a_boolean_is_not_a_whole_number():
    assert Field("count", kind="int").check(True) == "must be a whole number"


def test_a_value_outside_the_choices_is_reported():
    field = Field("size", choices=("small", "large"))
    assert field.check("medium") == "must be one of: small, large"
    assert field.check("large") is None
