"""Request handlers: coerce, validate, then answer."""

from schemacheck.coerce import coerce_payload
from schemacheck.errors import ValidationError

from .schemas import ORDER, SIGNUP


def create_account(form):
    """``(status, body)`` for a signup submission."""
    return _handle(SIGNUP, form)


def place_order(form):
    """``(status, body)`` for an order submission."""
    return _handle(ORDER, form)


def _handle(schema, form):
    payload = coerce_payload(schema, form)
    try:
        schema.validate(payload)
    except ValidationError as exc:
        return 400, {"errors": list(exc.errors)}
    return 201, payload
