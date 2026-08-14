"""Flatten and unflatten nested dictionaries."""


def flatten(data, parent="", sep="."):
    """Flatten a nested dict into dotted keys."""
    items = {}
    for key, value in data.items():
        full_key = f"{parent}{sep}{key}" if parent else key
        if isinstance(value, dict) and value:
            items.update(flatten(value, full_key, sep))
        else:
            items[key] = value
    return items


def get_path(data, path, sep="."):
    """Read a value from a nested dict by dotted path."""
    current = data
    for part in path.split(sep):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current
