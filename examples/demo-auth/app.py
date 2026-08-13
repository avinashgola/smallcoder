"""A deliberately buggy demo project for trying SmallCoder end-to-end.

Bug: emails are stored lowercased at registration, but login looks the email
up without normalizing case, so `Alice@Example.com` cannot log in.
"""

USERS: dict[str, str] = {}


def register(email: str, password: str) -> None:
    USERS[email.strip().lower()] = password


def login(email: str, password: str) -> bool:
    stored = USERS.get(email.strip())
    return stored is not None and stored == password
