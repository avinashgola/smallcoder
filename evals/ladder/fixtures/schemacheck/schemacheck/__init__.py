"""schemacheck -- describe the shape of a payload and check one against it.

Validation collects every problem it finds and reports them together, so a
form can be filled in once instead of once per mistake.
"""

from .coerce import coerce_payload, coerce_value
from .errors import SchemaError, ValidationError
from .fields import Field
from .schema import Schema, collect_errors

__all__ = [
    "coerce_payload",
    "coerce_value",
    "SchemaError",
    "ValidationError",
    "Field",
    "Schema",
    "collect_errors",
]
