"""Mapping task kinds onto the callables that execute them.

A handler is called as `handler(task, attempt_number)` and either returns a
value or raises. `attempt_number` is 1 on the first execution.
"""

from queueing.errors import QueueError


class Dispatcher:
    """A registry of handlers keyed by task kind."""

    def __init__(self, handlers=None):
        self._handlers = dict(handlers or {})
        self._fallback = None

    def register(self, kind, handler=None):
        """Register a handler; usable as a decorator when `handler` is omitted."""
        if handler is None:

            def decorator(func):
                self._handlers[kind] = func
                return func

            return decorator
        self._handlers[kind] = handler
        return handler

    def fallback(self, handler):
        """Handler used for kinds nothing else claims."""
        self._fallback = handler
        return handler

    def resolve(self, task):
        handler = self._handlers.get(task.kind, self._fallback)
        if handler is None:
            raise QueueError("no handler registered for kind %r" % (task.kind,))
        return handler

    def handles(self, kind):
        return kind in self._handlers or self._fallback is not None

    def kinds(self):
        return sorted(self._handlers)

    def unhandled(self, tasks):
        """Kinds among `tasks` that nothing can run."""
        return sorted({task.kind for task in tasks if not self.handles(task.kind)})
