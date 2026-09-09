"""Exceptions raised while declaring or checking blueprints."""


class BlueprintError(Exception):
    """Base class for everything this library raises."""


class FieldError(BlueprintError):
    """A field declaration is not something a blueprint can hold."""


class UnknownField(BlueprintError):
    """A blueprint was asked for a field it does not declare."""

    def __init__(self, blueprint, name):
        super().__init__("blueprint %r has no field %r" % (blueprint, name))
        self.blueprint = blueprint
        self.name = name


class ValidationError(BlueprintError):
    """A value does not satisfy the field it was offered to."""

    def __init__(self, name, message):
        super().__init__("%s: %s" % (name, message))
        self.name = name


class RecordNotFound(BlueprintError):
    """No record is stored under the requested id."""

    def __init__(self, record_id):
        super().__init__("no record with id %r" % (record_id,))
        self.record_id = record_id
