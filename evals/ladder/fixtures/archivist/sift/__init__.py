"""Filtering and ordering entries.

Rules describe what to keep; :mod:`sift.match` applies them and
:mod:`sift.order` puts the survivors in a defined order.

    from sift import HasTag, select

    select(depot.entries(), HasTag("home"))
"""

from .match import count_matching, first_match, partition, select
from .order import by_field, by_id, by_revision
from .phrases import parse_phrase
from .rules import (
    Every,
    FieldEquals,
    FieldMissing,
    FieldPresent,
    HasAllTags,
    HasTag,
    Rule,
    Some,
    TextContains,
    Unless,
)

__all__ = [
    "Rule",
    "HasTag",
    "HasAllTags",
    "FieldEquals",
    "FieldPresent",
    "FieldMissing",
    "TextContains",
    "Every",
    "Some",
    "Unless",
    "select",
    "first_match",
    "count_matching",
    "partition",
    "by_field",
    "by_revision",
    "by_id",
    "parse_phrase",
]
