"""Human-readable views of a loaded configuration."""

MASK = "***"


def redact(spec, values):
    """Copy of ``values`` with every secret field masked."""
    hidden = {field.name for field in spec if field.secret}
    return {
        name: (MASK if name in hidden and value is not None else value)
        for name, value in values.items()
    }


def describe(spec, values):
    """One ``NAME = value`` line per declared field, secrets masked."""
    safe = redact(spec, values)
    lines = []
    for field in spec:
        value = safe.get(field.name)
        if isinstance(value, tuple):
            value = ",".join(str(item) for item in value)
        lines.append(f"{spec.env_name(field)} = {value}")
    return lines


def missing_variables(environ, spec):
    """Names of the required variables that are not set."""
    absent = []
    for field in spec:
        if not field.required:
            continue
        raw = environ.get(spec.env_name(field))
        if raw is None or not raw.strip():
            absent.append(spec.env_name(field))
    return tuple(absent)
