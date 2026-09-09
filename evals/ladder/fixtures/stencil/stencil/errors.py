"""Exceptions raised while compiling or rendering a template."""


class TemplateError(Exception):
    """Base class for every error this package raises."""


class TemplateSyntaxError(TemplateError):
    """The template text could not be parsed."""


class UndefinedVariable(TemplateError):
    """A name used by the template is missing from the context."""

    def __init__(self, name):
        super().__init__("undefined variable: %s" % name)
        self.name = name


class UnknownFilter(TemplateError):
    """The template asked for a filter the environment does not know."""

    def __init__(self, name):
        super().__init__("unknown filter: %s" % name)
        self.name = name
