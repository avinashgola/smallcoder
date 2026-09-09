"""Individual constraints.

Every rule returns a message describing what is wrong, or ``None`` when the
value is acceptable.
"""


def not_blank(value):
    if not value.strip():
        return "must not be blank"
    return None


def min_length(value, limit):
    if len(value) < limit:
        return f"must be at least {limit} characters"
    return None


def max_length(value, limit):
    if len(value) > limit:
        return f"must be at most {limit} characters"
    return None


def minimum(value, limit):
    if value < limit:
        return f"must be {limit} or more"
    return None


def maximum(value, limit):
    if value > limit:
        return f"must be {limit} or less"
    return None


def one_of(value, choices):
    if value not in choices:
        allowed = ", ".join(str(choice) for choice in choices)
        return f"must be one of: {allowed}"
    return None


def looks_like_email(value):
    local, _, domain = value.partition("@")
    if not local or not domain or "." not in domain or domain.endswith("."):
        return "must look like an email address"
    return None
