import app


def setup_function() -> None:
    app.USERS.clear()


def test_login_lowercase() -> None:
    app.register("alice@example.com", "secret")
    assert app.login("alice@example.com", "secret")


def test_login_uppercase_email() -> None:
    app.register("alice@example.com", "secret")
    assert app.login("Alice@Example.COM", "secret")


def test_login_wrong_password() -> None:
    app.register("alice@example.com", "secret")
    assert not app.login("alice@example.com", "wrong")
