"""The layer protocol.

A layer is any callable taking ``(request, next_layer)`` and returning a
response.  Subclassing :class:`Layer` is optional; it only adds a name and a
readable repr for the debug endpoints.
"""


class Layer:
    """Convenience base class for middleware written as objects."""

    name = None

    def __call__(self, request, next_layer):
        raise NotImplementedError

    @property
    def label(self):
        return self.name or type(self).__name__

    def __repr__(self):
        return "<%s>" % self.label


class FunctionLayer(Layer):
    """Wraps a plain ``(request, next_layer)`` function so it has a label."""

    def __init__(self, func, name=None):
        self.func = func
        self.name = name or getattr(func, "__name__", "layer")

    def __call__(self, request, next_layer):
        return self.func(request, next_layer)


def as_layer(obj):
    """Validate that ``obj`` can act as a layer and return it unchanged."""
    if not callable(obj):
        raise TypeError("middleware must be callable, got %r"
                        % (type(obj).__name__,))
    return obj


def label_of(layer):
    """A short, stable name for a layer, used by the debug views."""
    if isinstance(layer, Layer):
        return layer.label
    return getattr(layer, "__name__", type(layer).__name__)
