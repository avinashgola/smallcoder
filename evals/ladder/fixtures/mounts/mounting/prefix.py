"""Prefix arithmetic shared by the mount table and the debug report."""


def normalize_prefix(prefix):
    """``''`` for a root mount, otherwise ``/admin`` with no trailing slash."""
    if not prefix or prefix == "/":
        return ""
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    while "//" in prefix:
        prefix = prefix.replace("//", "/")
    return prefix.rstrip("/")


def covers(path, prefix):
    """Whether ``path`` is the prefix itself or something below it."""
    if not prefix:
        return True
    return path == prefix or path.startswith(prefix + "/")


def join(prefix, path):
    """Glue a prefix and an inner path back into one outward-facing path."""
    prefix = normalize_prefix(prefix)
    if not path or path == "/":
        return prefix or "/"
    if not path.startswith("/"):
        path = "/" + path
    return (prefix + path) or "/"


def depth(prefix):
    """How many segments a prefix consumes; root mounts consume none."""
    return len([part for part in normalize_prefix(prefix).split("/") if part])
