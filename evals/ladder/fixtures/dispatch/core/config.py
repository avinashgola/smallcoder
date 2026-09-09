"""Settings for one application instance."""

DEFAULTS = {
    "debug": False,
    "server_name": "dispatch",
    "charset": "utf-8",
    "max_body_bytes": 1 << 20,
    "json_errors": True,
    "script_name": "",
}


class Config:
    """A validated settings bag with attribute access."""

    def __init__(self, **overrides):
        unknown = sorted(set(overrides) - set(DEFAULTS))
        if unknown:
            raise KeyError("unknown settings: " + ", ".join(unknown))
        values = dict(DEFAULTS)
        values.update(overrides)
        if values["max_body_bytes"] <= 0:
            raise ValueError("max_body_bytes must be positive")
        self.__dict__["_values"] = values

    def __getattr__(self, name):
        values = self.__dict__.get("_values", {})
        if name in values:
            return values[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name not in DEFAULTS:
            raise AttributeError("unknown setting %r" % (name,))
        self.__dict__["_values"][name] = value

    def __contains__(self, name):
        return name in self._values

    def get(self, name, default=None):
        return self._values.get(name, default)

    def as_dict(self):
        return dict(self._values)

    def replace(self, **overrides):
        merged = self.as_dict()
        merged.update(overrides)
        return Config(**merged)

    def __repr__(self):
        return "Config(%r)" % (sorted(self._values.items()),)
