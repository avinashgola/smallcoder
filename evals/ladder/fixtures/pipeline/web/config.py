"""Application settings."""

DEFAULTS = {
    "name": "pipeline",
    "debug": False,
    "default_charset": "utf-8",
    "max_body_bytes": 512 * 1024,
    "trusted_hosts": (),
}


class Settings:
    """Immutable settings with attribute access and a copy-on-change API."""

    def __init__(self, **overrides):
        unknown = sorted(set(overrides) - set(DEFAULTS))
        if unknown:
            raise KeyError("unknown settings: " + ", ".join(unknown))
        values = dict(DEFAULTS)
        values.update(overrides)
        if values["max_body_bytes"] < 0:
            raise ValueError("max_body_bytes cannot be negative")
        object.__setattr__(self, "_values", values)

    def __getattr__(self, name):
        values = object.__getattribute__(self, "_values")
        if name in values:
            return values[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        raise AttributeError("settings are immutable; use replace()")

    def replace(self, **overrides):
        merged = dict(object.__getattribute__(self, "_values"))
        merged.update(overrides)
        return Settings(**merged)

    def as_dict(self):
        return dict(object.__getattribute__(self, "_values"))

    def __repr__(self):
        return "Settings(%r)" % (sorted(self.as_dict().items()),)
