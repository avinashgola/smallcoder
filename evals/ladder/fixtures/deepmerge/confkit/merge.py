"""Combining configuration mappings."""


def merge(base, override):
    """Return a new mapping with ``override`` applied on top of ``base``.

    Nested mappings are merged key by key instead of being replaced wholesale,
    so a layer only has to restate the keys it actually changes.  A key whose
    override value is ``None`` means "this layer says nothing about it" and
    leaves the value underneath in place.
    """
    result = dict(base)
    for key, value in override.items():
        if not value:
            continue
        current = result.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            result[key] = merge(current, value)
        else:
            result[key] = value
    return result


def merge_all(mappings):
    """Fold :func:`merge` over an ordered sequence, lowest priority first."""
    result = {}
    for mapping in mappings:
        result = merge(result, mapping)
    return result


def prune(mapping):
    """Drop every key whose value is ``None``, recursively."""
    cleaned = {}
    for key, value in mapping.items():
        if value is None:
            continue
        cleaned[key] = prune(value) if isinstance(value, dict) else value
    return cleaned


def diff(base, other):
    """Return the part of ``other`` that differs from ``base``.

    Useful for showing what a layer actually contributes: the result is a
    mapping that, merged onto ``base``, reproduces ``other``'s changes.
    """
    changes = {}
    for key, value in other.items():
        current = base.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            nested = diff(current, value)
            if nested:
                changes[key] = nested
        elif current != value:
            changes[key] = value
    return changes
