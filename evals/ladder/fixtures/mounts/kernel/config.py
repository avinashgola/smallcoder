"""Per-application settings."""

DEFAULTS = {
    "debug": False,
    "json_errors": True,
    "trailing_slash_redirects": False,
    "server_token": "mounts",
}


class Settings:
    """A validated bag of settings."""

    def __init__(self, **overrides):
        unknown = sorted(set(overrides) - set(DEFAULTS))
        if unknown:
            raise KeyError("unknown settings: " + ", ".join(unknown))
        values = dict(DEFAULTS)
        values.update(overrides)
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

    def child(self, **overrides):
        """Settings for a mounted application, inheriting this one's values."""
        merged = dict(self.__dict__["_values"])
        merged.update(overrides)
        return Settings(**merged)

    def as_dict(self):
        return dict(self.__dict__["_values"])

    def __repr__(self):
        return "Settings(%r)" % (sorted(self.as_dict().items()),)
