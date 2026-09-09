"""The named shifts this rota is built from."""

from shifts.window import Window

TEMPLATES = {
    "early": Window.from_text("06:00-14:00"),
    "late": Window.from_text("14:00-22:00"),
    "night": Window.from_text("22:00-06:00"),
    "half": Window.from_text("09:00-13:00"),
}


class UnknownShift(ValueError):
    """Raised when a rota names a shift that does not exist."""


def names():
    return sorted(TEMPLATES)


def template(name):
    """The window a named shift covers."""
    key = str(name).strip().lower()
    if key not in TEMPLATES:
        raise UnknownShift("no such shift: %r" % (name,))
    return TEMPLATES[key]


def describe(name):
    key = str(name).strip().lower()
    return "%s %s" % (key, template(key).label())


def night_shifts():
    """The names of the shifts that run past midnight."""
    return sorted(key for key, window in TEMPLATES.items() if window.crosses_midnight)
