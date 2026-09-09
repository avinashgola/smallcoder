"""Server settings."""

from content.charset import DEFAULT, is_supported

SETTINGS = {
    "name": "negotiate",
    "charset": DEFAULT,
    "debug": False,
    "languages": ("en", "fr"),
}


class Settings:
    """Validated settings with attribute access."""

    def __init__(self, **overrides):
        unknown = sorted(set(overrides) - set(SETTINGS))
        if unknown:
            raise KeyError("unknown settings: " + ", ".join(unknown))
        values = dict(SETTINGS)
        values.update(overrides)
        if not is_supported(values["charset"]):
            raise ValueError("unsupported charset %r" % (values["charset"],))
        if not values["languages"]:
            raise ValueError("at least one language is required")
        self.__dict__["_values"] = values

    def __getattr__(self, name):
        values = self.__dict__.get("_values", {})
        if name in values:
            return values[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        raise AttributeError("settings are read only")

    def as_dict(self):
        return dict(self._values)

    def __repr__(self):
        return "Settings(%r)" % (sorted(self.as_dict().items()),)
