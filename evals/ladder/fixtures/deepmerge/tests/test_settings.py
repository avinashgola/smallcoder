from confkit.inifile import parse
from appconf.settings import origins, resolve

PRODUCTION = """
# report service, production profile
[server]
host = 0.0.0.0
workers = 8

[logging]
level = warning
debug = false

[http]
retries = 0
timeout = 5.0
"""


def test_defaults_apply_when_there_is_no_profile():
    settings = resolve()
    assert settings["server"]["port"] == 8080
    assert settings["logging"]["debug"] is True
    assert settings["http"]["retries"] == 3


def test_profile_replaces_the_values_it_names():
    settings = resolve(PRODUCTION)
    assert settings["server"]["host"] == "0.0.0.0"
    assert settings["server"]["workers"] == 8
    assert settings["logging"]["level"] == "warning"
    assert settings["http"]["timeout"] == 5.0


def test_profile_keeps_the_values_it_does_not_name():
    settings = resolve(PRODUCTION)
    assert settings["server"]["port"] == 8080
    assert settings["http"]["keepalive"] is True
    assert settings["features"]["export_csv"] is True


def test_profile_turns_debug_off():
    assert resolve(PRODUCTION)["logging"]["debug"] is False


def test_profile_can_disable_retries():
    assert resolve(PRODUCTION)["http"]["retries"] == 0


def test_command_line_beats_the_profile():
    settings = resolve(PRODUCTION, {"server.port": 9001, "logging.level": "debug"})
    assert settings["server"]["port"] == 9001
    assert settings["logging"]["level"] == "debug"
    assert settings["server"]["host"] == "0.0.0.0"


def test_origins_name_the_winning_layer():
    where = origins(PRODUCTION, {"server.port": 9001})
    assert where["server.host"] == "profile"
    assert where["server.port"] == "cli"
    assert where["features.export_csv"] == "defaults"


def test_parser_understands_dotted_options_and_comments():
    parsed = parse("[cache]\nredis.db = 2  # second database\nenabled = yes\n")
    assert parsed == {"cache": {"redis": {"db": 2}, "enabled": True}}
