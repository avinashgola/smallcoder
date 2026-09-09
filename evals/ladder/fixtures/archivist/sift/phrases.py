"""A one-line query language for the sift layer.

    tag:home            entries carrying the tag
    -tag:home           entries not carrying it
    minutes=0           a field with exactly that value
    title~radiator      a field containing that text
    note?               the field is present, whatever it holds
    note!               the field is absent

Terms are separated by spaces and every term has to hold.  Values are
read as numbers when they look like numbers, as ``true``/``false`` when
they look like booleans, and as text otherwise.
"""

from depot.errors import FieldError

from .rules import (
    Every,
    FieldEquals,
    FieldMissing,
    FieldPresent,
    HasTag,
    TextContains,
    Unless,
)


def parse_value(text):
    """Read a written value: a number, a boolean or plain text."""
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return text


def parse_term(term):
    """Turn one written term into a rule."""
    if not term:
        raise FieldError("empty term")
    if term.startswith("-"):
        return Unless(parse_term(term[1:]))
    if term.startswith("tag:"):
        return HasTag(term[4:])
    if "~" in term:
        name, fragment = term.split("~", 1)
        if not name or not fragment:
            raise FieldError("bad text term %r" % (term,))
        return TextContains(name, fragment)
    if "=" in term:
        name, value = term.split("=", 1)
        if not name:
            raise FieldError("bad field term %r" % (term,))
        return FieldEquals(name, parse_value(value))
    if term.endswith("?"):
        return FieldPresent(term[:-1])
    if term.endswith("!"):
        return FieldMissing(term[:-1])
    raise FieldError("cannot read the term %r" % (term,))


def parse_phrase(text):
    """Turn a whole phrase into one rule."""
    terms = [term for term in text.split() if term]
    if not terms:
        raise FieldError("an empty phrase would match everything; say so explicitly")
    rules = [parse_term(term) for term in terms]
    if len(rules) == 1:
        return rules[0]
    return Every(rules)
