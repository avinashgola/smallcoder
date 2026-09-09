"""Turn the strings a form or query string delivers into typed values.

Anything that cannot be converted is passed through unchanged so that
validation reports it, rather than raising here.
"""

TRUE_WORDS = frozenset({"1", "true", "yes", "on"})
FALSE_WORDS = frozenset({"0", "false", "no", "off"})


def coerce_value(field, raw):
    """Convert one raw value to the kind the field declares."""
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    if field.kind == "int":
        try:
            return int(text, 10)
        except ValueError:
            return text
    if field.kind == "bool":
        lowered = text.lower()
        if lowered in TRUE_WORDS:
            return True
        if lowered in FALSE_WORDS:
            return False
        return text
    return text


def coerce_payload(schema, raw):
    """Coerce the fields the schema declares; leave everything else alone."""
    coerced = {}
    for key, value in raw.items():
        try:
            field = schema.field(key)
        except KeyError:
            coerced[key] = value
            continue
        coerced[key] = coerce_value(field, value)
    return coerced
