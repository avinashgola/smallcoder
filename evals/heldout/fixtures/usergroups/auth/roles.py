"""Role definitions and inheritance."""

ROLE_PERMISSIONS = {
    "viewer": {"read"},
    "editor": {"read", "write"},
    "admin": {"read", "write", "delete", "manage_users"},
}

ROLE_ORDER = ["viewer", "editor", "admin"]


def permissions_for(role):
    if role not in ROLE_PERMISSIONS:
        raise KeyError(f"unknown role: {role}")
    return set(ROLE_PERMISSIONS[role])


def rank(role):
    return ROLE_ORDER.index(role)
