"""A minimal synchronous event bus.

The runner emits an event at every job transition. Reporters, metrics and
tests subscribe to those events instead of wrapping the runner.
"""

EVENTS = ("run_start", "job_start", "job_success", "job_failure", "job_skip", "run_end")


class HookBus:
    """Fan out events to callbacks, in subscription order."""

    def __init__(self):
        self._subscribers = {name: [] for name in EVENTS}

    def subscribe(self, event, callback):
        if event not in self._subscribers:
            raise ValueError("unknown event %r" % (event,))
        self._subscribers[event].append(callback)
        return callback

    def on(self, event):
        """Decorator form of `subscribe`."""

        def register(callback):
            self.subscribe(event, callback)
            return callback

        return register

    def emit(self, event, **payload):
        if event not in self._subscribers:
            raise ValueError("unknown event %r" % (event,))
        for callback in self._subscribers[event]:
            callback(**payload)

    def subscriber_count(self, event):
        return len(self._subscribers[event])


class EventLog:
    """Records every event it is subscribed to; handy in tests and reports."""

    def __init__(self, bus=None):
        self.entries = []
        if bus is not None:
            self.attach(bus)

    def attach(self, bus):
        for event in EVENTS:
            bus.subscribe(event, self._make_handler(event))
        return self

    def _make_handler(self, event):
        def handler(**payload):
            self.entries.append((event, payload))

        return handler

    def events_named(self, event):
        return [payload for name, payload in self.entries if name == event]

    def job_ids_for(self, event):
        return [payload.get("job_id") for payload in self.events_named(event)]
