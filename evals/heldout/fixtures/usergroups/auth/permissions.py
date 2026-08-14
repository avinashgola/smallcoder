"""Effective permission resolution across a user's roles."""

from auth.roles import permissions_for


def effective_permissions(roles):
    """Union of the permissions granted by all of a user's roles."""
    granted = set()
    for role in roles:
        granted &= permissions_for(role)
    return granted


def can(user_roles, permission):
    return permission in effective_permissions(user_roles)
