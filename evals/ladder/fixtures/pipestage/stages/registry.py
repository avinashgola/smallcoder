"""Creating stages from plain configuration dictionaries."""

from common.errors import ConfigError
from common.validators import non_empty_string, require_keys


class StageRegistry:
    """Maps a `type` string in a plan onto a stage factory."""

    def __init__(self, factories=None):
        self._factories = dict(factories or {})

    def register(self, kind, factory=None):
        """Register a factory; usable as a decorator when `factory` is omitted."""
        if factory is None:

            def decorator(func):
                self._factories[kind] = func
                return func

            return decorator
        self._factories[kind] = factory
        return factory

    def knows(self, kind):
        return kind in self._factories

    def kinds(self):
        return sorted(self._factories)

    def create(self, config):
        """Build one stage from `{"type": ..., "name": ..., **options}`."""
        config = dict(config)
        require_keys(config, ["type", "name"], where="stage config")
        kind = non_empty_string(config.pop("type"), "type", where="stage config")
        name = non_empty_string(config.pop("name"), "name", where="stage config")
        if kind not in self._factories:
            raise ConfigError(
                "unknown stage type %r (known: %s)" % (kind, ", ".join(self.kinds())),
                where=name,
            )
        try:
            return self._factories[kind](name=name, **config)
        except TypeError as exc:
            raise ConfigError("bad options for %r: %s" % (kind, exc), where=name)

    def create_all(self, configs):
        return [self.create(config) for config in configs]

    def merged(self, other):
        """A registry knowing the factories of both."""
        combined = dict(self._factories)
        combined.update(other._factories)
        return StageRegistry(combined)
