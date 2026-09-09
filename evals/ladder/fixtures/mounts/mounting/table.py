"""The table of mounted applications."""

from .prefix import covers, normalize_prefix


class Mount:
    """One application bound to a path prefix."""

    def __init__(self, prefix, app, name=None):
        self.prefix = normalize_prefix(prefix)
        self.app = app
        self.name = name or getattr(app, "name", None) or self.prefix or "root"

    @property
    def is_root(self):
        """A root mount consumes nothing and sees the path unchanged."""
        return self.prefix == ""

    def covers(self, path):
        return covers(path, self.prefix)

    def __repr__(self):
        return "<Mount %s -> %s>" % (self.prefix or "/", self.name)


class MountTable:
    """Mounts searched longest prefix first, registration order breaking ties."""

    def __init__(self):
        self._mounts = []

    def __len__(self):
        return len(self._mounts)

    def __iter__(self):
        return iter(self._mounts)

    def add(self, prefix, app, name=None):
        mount = Mount(prefix, app, name)
        if any(existing.prefix == mount.prefix for existing in self._mounts):
            raise ValueError("%r is already mounted" % (mount.prefix or "/",))
        self._mounts.append(mount)
        return mount

    def ordered(self):
        """Mounts from the most specific prefix to the least."""
        return sorted(self._mounts, key=lambda mount: -len(mount.prefix))

    def resolve(self, path):
        """Find the mount serving ``path``.

        Returns ``(mount, inner_path)`` where ``inner_path`` is what the
        mounted application should be asked for, or ``None`` when no mount
        covers the path.
        """
        for mount in self.ordered():
            if not mount.covers(path):
                continue
            if mount.is_root:
                return mount, path
            rest = path[len(mount.prefix) + 1:]
            return mount, rest
        return None

    def named(self, name):
        for mount in self._mounts:
            if mount.name == name:
                return mount
        raise KeyError(name)

    def prefixes(self):
        return [mount.prefix or "/" for mount in self._mounts]
