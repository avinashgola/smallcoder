"""A very small text template engine.

Templates use `{{ name }}` for substitution, `{{ name|filter }}` to run a
value through a filter, and `{% if x %}` / `{% for x in xs %}` blocks.
"""

from .environment import Environment, render
from .errors import TemplateError, TemplateSyntaxError, UndefinedVariable

__all__ = [
    "Environment",
    "TemplateError",
    "TemplateSyntaxError",
    "UndefinedVariable",
    "render",
]
