"""Exceptions raised while checking a payload."""


class SchemaError(Exception):
    """Base class for every error raised here."""


class ValidationError(SchemaError):
    """A payload did not match its schema.

    ``errors`` holds one message per problem, in the order the schema declares
    its fields.
    """

    def __init__(self, schema_name, errors):
        joined = "; ".join(errors)
        super().__init__(f"{schema_name}: {joined}")
        self.schema_name = schema_name
        self.errors = tuple(errors)
