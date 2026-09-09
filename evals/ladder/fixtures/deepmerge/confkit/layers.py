"""An ordered stack of configuration layers."""

from .errors import InvalidLayer, MissingKey
from .merge import merge_all
from .paths import get, has

_MISSING = object()


class Layer:
    """One named contribution to the configuration."""

    def __init__(self, name, data):
        if not isinstance(data, dict):
            raise InvalidLayer(f"layer {name!r} is not a mapping")
        self.name = name
        self.data = data

    def __repr__(self):
        return f"Layer({self.name!r}, {len(self.data)} keys)"


class LayerStack:
    """Layers in priority order: the last one added wins."""

    def __init__(self):
        self._layers = []

    def add(self, name, data):
        self._layers.append(Layer(name, data))
        return self

    @property
    def names(self):
        return [layer.name for layer in self._layers]

    def resolve(self):
        """Collapse every layer into a single mapping."""
        return merge_all([layer.data for layer in self._layers])

    def get(self, path, default=_MISSING):
        resolved = self.resolve()
        if default is _MISSING:
            return get(resolved, path)
        return get(resolved, path, default)

    def origin(self, path):
        """Name of the highest-priority layer that supplies ``path``."""
        for layer in reversed(self._layers):
            if has(layer.data, path) and get(layer.data, path) is not None:
                return layer.name
        raise MissingKey(path)
