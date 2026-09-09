"""Small argument checks shared by every stage constructor."""

from common.errors import ConfigError


def require_keys(mapping, keys, where="config"):
    """Every key in `keys` must be present in `mapping`."""
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise ConfigError("missing keys: " + ", ".join(sorted(missing)), where)
    return mapping


def reject_keys(mapping, allowed, where="config"):
    """No key outside `allowed` may be present."""
    unknown = sorted(set(mapping) - set(allowed))
    if unknown:
        raise ConfigError("unknown keys: " + ", ".join(unknown), where)
    return mapping


def ensure_type(value, types, name, where=None):
    if not isinstance(value, types):
        names = getattr(types, "__name__", None) or "/".join(
            t.__name__ for t in types
        )
        raise ConfigError("%s must be a %s" % (name, names), where)
    return value


def positive_int(value, name, where=None):
    ensure_type(value, int, name, where)
    if value <= 0:
        raise ConfigError("%s must be greater than zero" % (name,), where)
    return value


def one_of(value, choices, name, where=None):
    if value not in choices:
        raise ConfigError(
            "%s must be one of %s" % (name, ", ".join(sorted(choices))), where
        )
    return value


def non_empty_string(value, name, where=None):
    ensure_type(value, str, name, where)
    if not value.strip():
        raise ConfigError("%s must not be empty" % (name,), where)
    return value.strip()
