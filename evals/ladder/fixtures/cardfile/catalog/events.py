"""A small append-only log of the mutations a store has seen."""


class EventLog:
    """Holds ``(kind, record_id)`` pairs in the order they happened.

    The log is bounded: once it grows past ``limit`` the oldest entries are
    dropped, which keeps a long-lived store from leaking memory.
    """

    def __init__(self, limit=256):
        self._entries = []
        self._listeners = []
        self.limit = limit

    def append(self, kind, record_id):
        self._entries.append((kind, record_id))
        overflow = len(self._entries) - self.limit
        if overflow > 0:
            del self._entries[:overflow]
        for listener in list(self._listeners):
            listener(kind, record_id)

    def subscribe(self, listener):
        self._listeners.append(listener)
        return listener

    def unsubscribe(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def entries(self, kind=None):
        if kind is None:
            return list(self._entries)
        return [entry for entry in self._entries if entry[0] == kind]

    def kinds(self):
        return sorted({kind for kind, _ in self._entries})

    def count(self, kind=None):
        return len(self.entries(kind))

    def last(self):
        return self._entries[-1] if self._entries else None

    def clear(self):
        self._entries = []

    def __len__(self):
        return len(self._entries)
