"""The payloads this service accepts."""

from schemacheck.fields import Field
from schemacheck.schema import Schema

SHIPPING_METHODS = ("standard", "express")

SIGNUP = Schema(
    "signup",
    (
        Field("name", min_length=2, max_length=40),
        Field("email", email=True),
        Field("age", kind="int", required=False, minimum=13, maximum=120),
        Field("newsletter", kind="bool", required=False),
    ),
)

ORDER = Schema(
    "order",
    (
        Field("sku", min_length=3, max_length=16),
        Field("quantity", kind="int", minimum=1, maximum=99),
        Field("shipping", choices=SHIPPING_METHODS),
        Field("gift_note", required=False, max_length=120),
    ),
)
