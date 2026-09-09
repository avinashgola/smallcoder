"""Default values applied to every job entry in a specification."""

DEFAULT_JOB = {
    "action": "noop",
    "params": {},
    "after": [],
    "tags": [],
    "critical": True,
}

KNOWN_JOB_KEYS = frozenset(DEFAULT_JOB) | {"id"}
KNOWN_SPEC_KEYS = frozenset({"name", "jobs", "groups", "defaults"})


def apply_defaults(entry, overrides=None):
    """Fill in the keys a job entry left out."""
    merged = dict(DEFAULT_JOB)
    merged.update(overrides or {})
    for key, value in entry.items():
        if value is not None:
            merged[key] = value
    merged["params"] = dict(merged.get("params") or {})
    merged["after"] = list(merged.get("after") or [])
    merged["tags"] = list(merged.get("tags") or [])
    merged["critical"] = bool(merged.get("critical", True))
    return merged


def spec_defaults(spec):
    """Per spec overrides for the job defaults, if any were declared."""
    overrides = spec.get("defaults") or {}
    return {key: value for key, value in overrides.items() if key in DEFAULT_JOB}
