from settings import DEFAULTS, load_settings, parse_bool


def test_defaults():
    assert load_settings({}) == DEFAULTS


def test_parse_bool_truthy_words():
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("yes") is True


def test_parse_bool_falsy_words():
    assert parse_bool("false") is False
    assert parse_bool("False") is False
    assert parse_bool("0") is False
    assert parse_bool("no") is False
    assert parse_bool("") is False


def test_debug_disabled_via_env():
    assert load_settings({"APP_DEBUG": "false"})["debug"] is False
    assert load_settings({"APP_DEBUG": "0"})["debug"] is False


def test_debug_enabled_via_env():
    assert load_settings({"APP_DEBUG": "true"})["debug"] is True


def test_numeric_overrides():
    settings = load_settings({"APP_TIMEOUT": "5", "APP_RETRIES": "1"})
    assert settings["timeout"] == 5
    assert settings["retries"] == 1
