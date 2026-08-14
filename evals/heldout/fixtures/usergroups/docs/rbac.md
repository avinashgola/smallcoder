# Role-based access control

Users may hold several roles at once. A user's effective permission set is the
**union** of the permissions granted by each of their roles: holding an extra
role can only ever grant more access, never less.

Roles are defined in `auth/roles.py`. Session handling (`auth/session.py`) and
the audit trail (`auth/audit.py`) are independent subsystems.
