from auth.session import Session


def test_not_expired():
    assert not Session("u1", 0).is_expired(10)


def test_expired():
    assert Session("u1", 0).is_expired(3600)


def test_remaining():
    assert Session("u1", 0).remaining(600) == 3000
