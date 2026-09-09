"""Blueprints: the declared shape of the records a cabinet holds.

A :class:`~blueprint.forms.Blueprint` is a named list of
:class:`~blueprint.fields.Field` declarations.  Each field knows its type,
whether it may be left out and what an unset copy of it looks like.

    task = Blueprint("task", [
        Field("title", "text", required=True),
        Field("tags", "list"),
        Field("minutes", "number"),
    ])

Blueprints hold no data themselves; a cabinet uses them to build records.
"""

from .defaults import blank_for, clone_default
from .errors import BlueprintError, FieldError, UnknownField, ValidationError
from .fields import Field
from .forms import Blueprint
from .registry import Registry

__all__ = [
    "Field",
    "Blueprint",
    "Registry",
    "blank_for",
    "clone_default",
    "BlueprintError",
    "FieldError",
    "UnknownField",
    "ValidationError",
]
