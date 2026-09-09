"""Read a :class:`~envcfg.spec.Spec` out of an environment mapping."""

from .casters import cast
from .errors import MissingSetting


def load(environ, spec, overrides={}):
    """Return ``{field name: value}`` for every field the spec declares.

    ``overrides`` holds values that were already decided elsewhere -- command
    line flags, say -- and they win over the environment without being cast
    again.  The caller's mapping is only read, never written to, and each call
    starts from nothing but the spec and the arguments it was given.
    """
    values = overrides
    for field in spec:
        if field.name in values:
            continue
        raw = environ.get(spec.env_name(field))
        if raw is None or not raw.strip():
            if field.required:
                raise MissingSetting(spec.env_name(field))
            values[field.name] = field.default
            continue
        values[field.name] = cast(field.kind, raw, where=spec.env_name(field))
    spec.check(values)
    return values


def load_many(environ, specs):
    """Load several specs into one mapping keyed by prefix."""
    return {spec.prefix: load(environ, spec, {}) for spec in specs}
