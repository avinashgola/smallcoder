"""Handlers written as objects, one method per HTTP verb."""

from .errors import MethodNotAllowed

VERBS = ("GET", "POST", "PUT", "PATCH", "DELETE")


class MethodView:
    """A handler that dispatches on the request method.

    Define ``get``, ``post`` and friends; the verbs a subclass implements are
    the verbs its route accepts.  ``HEAD`` is served by ``get``.
    """

    def __call__(self, request):
        verb = "get" if request.method == "HEAD" else request.method.lower()
        handler = getattr(self, verb, None)
        if handler is None:
            raise MethodNotAllowed(self.allowed())
        return handler(request)

    @classmethod
    def allowed(cls):
        """The verbs this class implements, in a stable order."""
        return [verb for verb in VERBS if hasattr(cls, verb.lower())]

    @classmethod
    def attach(cls, app, template, name=None, **kwargs):
        """Build one instance and register it as a route on ``app``."""
        view = cls(**kwargs)
        return app.route(template, view, cls.allowed(), name or cls.__name__)

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, "|".join(self.allowed()))
