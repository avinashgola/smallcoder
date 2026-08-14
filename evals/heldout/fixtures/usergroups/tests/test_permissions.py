from auth.permissions import can, effective_permissions


def test_single_role():
    assert effective_permissions(["viewer"]) == {"read"}


def test_multiple_roles_are_combined():
    assert effective_permissions(["viewer", "editor"]) == {"read", "write"}


def test_admin_plus_viewer_keeps_admin_powers():
    perms = effective_permissions(["viewer", "admin"])
    assert "delete" in perms
    assert "manage_users" in perms


def test_no_roles_grants_nothing():
    assert effective_permissions([]) == set()


def test_can_helper():
    assert can(["editor"], "write")
    assert not can(["viewer"], "write")
    assert can(["viewer", "admin"], "manage_users")
