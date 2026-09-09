"""The public entry point for rendering templates."""

from .filters import DEFAULT_FILTERS
from .parser import parse
from .renderer import render_nodes


class Environment:
    """Holds the defaults and filters a group of templates renders with.

    Values passed to `render` win over anything registered on the
    environment, so a default acts as a fallback rather than an override.
    """

    def __init__(self, defaults={}):
        self.defaults = defaults
        self.filters = dict(DEFAULT_FILTERS)
        self._compiled = {}

    def register(self, name, value):
        """Make `name` visible to every template rendered by this environment."""
        self.defaults[name] = value

    def add_filter(self, name, function):
        """Teach this environment a new `{{ x|name }}` filter."""
        self.filters[name] = function

    def compile(self, source):
        """Parse `source`, reusing the node tree on repeat renders."""
        if source not in self._compiled:
            self._compiled[source] = parse(source)
        return self._compiled[source]

    def render(self, source, context=None):
        """Render `source` against `context` plus this environment's defaults."""
        scope = dict(self.defaults)
        scope.update(context or {})
        return render_nodes(self.compile(source), scope, self.filters)


def render(source, context=None):
    """Render one template with a throwaway environment."""
    return Environment().render(source, context)
