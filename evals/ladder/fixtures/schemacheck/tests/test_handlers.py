from api.handlers import create_account, place_order

SIGNUP_FORM = {
    "name": "Ada",
    "email": "ada@example.com",
    "age": "36",
    "newsletter": "yes",
}
ORDER_FORM = {"sku": "widget-1", "quantity": "2", "shipping": "express"}


def test_a_good_signup_is_accepted_and_coerced():
    status, body = create_account(SIGNUP_FORM)
    assert status == 201
    assert body == {
        "name": "Ada",
        "email": "ada@example.com",
        "age": 36,
        "newsletter": True,
    }


def test_a_good_order_is_accepted():
    status, body = place_order(ORDER_FORM)
    assert status == 201
    assert body["quantity"] == 2


def test_a_bad_email_is_rejected_even_though_the_name_is_fine():
    status, body = create_account({"name": "Ada", "email": "ada@"})
    assert status == 400
    assert body == {"errors": ["email: must look like an email address"]}


def test_every_problem_with_a_form_comes_back_at_once():
    status, body = place_order(dict(ORDER_FORM, quantity="0", shipping="drone"))
    assert status == 400
    assert body["errors"] == [
        "quantity: must be 1 or more",
        "shipping: must be one of: standard, express",
    ]


def test_a_quantity_that_is_not_a_number_is_reported():
    status, body = place_order(dict(ORDER_FORM, quantity="many"))
    assert status == 400
    assert body["errors"] == ["quantity: must be a int"]


def test_a_form_field_nobody_declared_is_rejected():
    status, body = place_order(dict(ORDER_FORM, coupon="SAVE10"))
    assert status == 400
    assert body["errors"] == ["coupon: unknown field"]


def test_missing_form_fields_are_listed():
    status, body = place_order({})
    assert status == 400
    assert body["errors"] == [
        "sku: this field is required",
        "quantity: this field is required",
        "shipping: this field is required",
    ]


def test_the_optional_note_still_has_a_length_limit():
    status, body = place_order(dict(ORDER_FORM, gift_note="x" * 121))
    assert status == 400
    assert body["errors"] == ["gift_note: must be at most 120 characters"]
