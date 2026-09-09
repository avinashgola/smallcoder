"""The filters every environment starts with."""

from .numbers import comma, percent, plural, round_to
from .text import lower, title, trim, truncate, upper

DEFAULT_FILTERS = {
    "comma": comma,
    "lower": lower,
    "percent": percent,
    "plural": plural,
    "round": round_to,
    "title": title,
    "trim": trim,
    "truncate": truncate,
    "upper": upper,
}

__all__ = ["DEFAULT_FILTERS"]
