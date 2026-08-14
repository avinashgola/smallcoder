"""Audit trail helpers (unrelated to permission resolution)."""


def format_event(actor, action, target):
    return f"{actor} {action} {target}"


def filter_events(events, actor):
    return [e for e in events if e.startswith(f"{actor} ")]
