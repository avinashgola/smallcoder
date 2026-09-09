"""Dotted-path access into nested configuration mappings."""

from .errors import MissingKey

_MISSING = object()


def split(path):
    """Split ``"server.bind.port"`` into ``["server", "bind", "port"]``."""
    parts = [part.strip() for part in path.split(".")]
    if not all(parts):
        raise MissingKey(path)
    return parts


def get(mapping, path, default=_MISSING):
    """Look up a dotted path, raising :class:`MissingKey` without a default."""
    node = mapping
    for part in split(path):
        if not isinstance(node, dict) or part not in node:
            if default is _MISSING:
                raise MissingKey(path)
            return default
        node = node[part]
    return node


def has(mapping, path):
    """True when ``path`` resolves to something in ``mapping``."""
    try:
        get(mapping, path)
    except MissingKey:
        return False
    return True


def assign(mapping, path, value):
    """Return a copy of ``mapping`` with ``path`` set to ``value``."""
    parts = split(path)
    root = dict(mapping)
    node = root
    for part in parts[:-1]:
        child = node.get(part)
        node[part] = dict(child) if isinstance(child, dict) else {}
        node = node[part]
    node[parts[-1]] = value
    return root


def flatten(mapping, prefix=""):
    """Turn a nested mapping into ``{"a.b": value}`` form."""
    flat = {}
    for key, value in mapping.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            flat.update(flatten(value, prefix=f"{path}."))
        else:
            flat[path] = value
    return flat


def expand(flat):
    """Inverse of :func:`flatten`."""
    nested = {}
    for path, value in flat.items():
        nested = assign(nested, path, value)
    return nested
