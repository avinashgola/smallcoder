"""Semantic-version parsing and comparison helpers for the updater."""


def parse_version(version):
    """Parse a 'MAJOR.MINOR.PATCH' string into a comparable tuple."""
    parts = version.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"not a semantic version: {version!r}")
    return tuple(parts)


def is_newer(candidate, current):
    """True if candidate is a strictly newer version than current."""
    return parse_version(candidate) > parse_version(current)


def latest(versions):
    """Return the newest version string from a non-empty list."""
    if not versions:
        raise ValueError("no versions given")
    best = versions[0]
    for version in versions[1:]:
        if is_newer(version, best):
            best = version
    return best
