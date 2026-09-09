"""The middleware chain: how layers are ordered and wrapped."""

from .base import as_layer, label_of


class Chain:
    """An ordered stack of layers that wraps a single endpoint.

    The first layer added is the outermost one: it sees the request before
    every other layer does and the response after all of them have run.
    """

    def __init__(self, layers=[]):
        self.layers = layers

    def __len__(self):
        return len(self.layers)

    def __iter__(self):
        return iter(self.layers)

    def __contains__(self, layer):
        return layer in self.layers

    def add(self, layer):
        """Append a layer, making it the innermost one so far."""
        self.layers.append(as_layer(layer))
        return self

    def prepend(self, layer):
        """Insert a layer in front of every layer added so far."""
        self.layers.insert(0, as_layer(layer))
        return self

    def extend(self, layers):
        for layer in layers:
            self.add(layer)
        return self

    def discard(self, layer):
        if layer in self.layers:
            self.layers.remove(layer)
        return self

    def labels(self):
        return [label_of(layer) for layer in self.layers]

    def build(self, endpoint):
        """Compose the layers around ``endpoint`` into one callable."""
        handler = endpoint
        for layer in reversed(self.layers):
            handler = _bind(layer, handler)
        return handler

    def copy(self):
        return Chain(list(self.layers))

    def __repr__(self):
        return "Chain(%r)" % (self.labels(),)


def _bind(layer, next_layer):
    def call(request):
        return layer(request, next_layer)

    call.layer = layer
    return call
