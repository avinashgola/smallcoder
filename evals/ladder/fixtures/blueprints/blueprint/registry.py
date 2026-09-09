"""The blueprints a cabinet knows about."""

from .errors import BlueprintError
from .forms import Blueprint


class Registry:
    """A name -> blueprint mapping, with no two blueprints per name."""

    def __init__(self, blueprints=()):
        self._blueprints = {}
        for blueprint in blueprints:
            self.register(blueprint)

    def register(self, blueprint):
        if not isinstance(blueprint, Blueprint):
            raise BlueprintError("expected a Blueprint, got %r" % (blueprint,))
        if blueprint.name in self._blueprints:
            raise BlueprintError("blueprint %r is already registered" % (blueprint.name,))
        self._blueprints[blueprint.name] = blueprint
        return blueprint

    def get(self, name):
        try:
            return self._blueprints[name]
        except KeyError:
            raise BlueprintError("no blueprint named %r" % (name,))

    def has(self, name):
        return name in self._blueprints

    def names(self):
        return sorted(self._blueprints)

    def describe(self):
        return [self._blueprints[name].describe() for name in self.names()]

    def __len__(self):
        return len(self._blueprints)

    def __iter__(self):
        return iter(self.get(name) for name in self.names())
