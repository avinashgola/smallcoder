import pytest

from envcfg.errors import MissingSetting
from envcfg.report import redact
from service.bootstrap import configure, preflight, summary
from service.spec import SERVICE_SPEC

BASE = {"APP_DATABASE_URL": "postgres://db/reports"}


def test_defaults_for_a_bare_environment():
    values = configure(BASE)
    assert values["host"] == "127.0.0.1"
    assert values["port"] == 8080
    assert values["debug"] is False
    assert values["bind"] == "127.0.0.1:8080"


def test_values_are_cast_to_their_declared_types():
    env = dict(BASE, APP_PORT="9090", APP_DEBUG="yes", APP_REQUEST_TIMEOUT="2.5")
    values = configure(env)
    assert values["port"] == 9090
    assert values["debug"] is True
    assert values["request_timeout"] == 2.5


def test_list_values_split_on_commas():
    env = dict(BASE, APP_ALLOWED_ORIGINS="a.example , b.example ,")
    assert configure(env)["allowed_origins"] == ("a.example", "b.example")


def test_flags_beat_the_environment():
    env = dict(BASE, APP_PORT="9090")
    assert configure(env, port=7000)["port"] == 7000


def test_missing_database_url_stops_start_up():
    with pytest.raises(MissingSetting):
        configure({})


def test_preflight_lists_what_is_not_set():
    assert preflight({}) == ("APP_DATABASE_URL",)
    assert preflight(BASE) == ()


def test_summary_masks_the_secret():
    lines = summary(configure(BASE))
    assert "APP_DATABASE_URL = ***" in lines
    assert "APP_PORT = 8080" in lines


def test_redact_leaves_ordinary_values_alone():
    assert redact(SERVICE_SPEC, configure(BASE))["host"] == "127.0.0.1"
