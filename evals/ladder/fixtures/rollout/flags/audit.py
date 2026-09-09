"""Explain a flag decision in words, for support and for the admin page."""

from .bucket import bucket_of


def explain(flag, subject):
    """One line saying why ``flag`` is on or off for ``subject``."""
    if not flag.enabled:
        return f"{flag.name}: off (the flag is switched off)"
    if subject in flag.deny:
        return f"{flag.name}: off (on the deny list)"
    if subject in flag.allow:
        return f"{flag.name}: on (on the allow list)"
    state = "on" if flag.decide(subject) else "off"
    bucket = bucket_of(flag.name, subject)
    return f"{flag.name}: {state} (bucket {bucket}, rollout {flag.percent}%)"


def report(registry, subject):
    """An explanation for every flag, in the registry's stable order."""
    return [explain(registry.get(name), subject) for name in registry.names()]
