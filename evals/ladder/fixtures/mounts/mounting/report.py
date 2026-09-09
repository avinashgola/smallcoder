"""A readable description of what is mounted where."""

from .prefix import join


def walk(app, prefix=""):
    """Yield ``(outward_prefix, application)`` for an app and its mounts."""
    yield prefix, app
    for mount in getattr(app, "mounts", ()):  # leaves have no mount table
        yield from walk(mount.app, join(prefix, mount.prefix or "/"))


def describe(app, prefix=""):
    """A JSON-able tree of every mounted application and its routes."""
    entries = []
    for outward, mounted in walk(app, prefix):
        entries.append({
            "prefix": outward or "/",
            "app": getattr(mounted, "name", type(mounted).__name__),
            "routes": [join(outward, source)
                       for source in mounted.router.sources()],
        })
    return entries


def render(app):
    """The same information as flat text, for logs."""
    lines = []
    for entry in describe(app):
        lines.append("%s (%s)" % (entry["prefix"], entry["app"]))
        for route in entry["routes"]:
            lines.append("  " + route)
    return "\n".join(lines)
