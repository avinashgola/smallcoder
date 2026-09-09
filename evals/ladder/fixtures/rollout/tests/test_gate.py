import pytest

from flags.errors import FlagDefinitionError, UnknownFlag
from flags.registry import Registry, parse_definitions
from app.gate import active_features, can_use, require, status_page, why


def test_the_flag_file_is_read_correctly():
    definitions = parse_definitions("dark_mode: 50%\nold_ui: off deny=user-2\n")
    assert definitions == {
        "dark_mode": {"percent": 50},
        "old_ui": {"enabled": False, "deny": ["user-2"]},
    }


def test_an_unreadable_flag_file_line_is_rejected():
    with pytest.raises(FlagDefinitionError):
        parse_definitions("dark_mode: sometimes\n")


def test_a_switched_off_flag_is_off_even_at_full_rollout():
    assert can_use("user-1", "beta_search") is False


def test_the_allow_list_wins_over_a_zero_rollout():
    assert can_use("user-7", "csv_export") is True


def test_the_deny_list_wins_over_a_full_rollout():
    assert can_use("user-13", "new_editor") is False
    assert can_use("user-1", "new_editor") is True


def test_a_flag_staged_at_zero_percent_is_off_for_everyone():
    users = [f"user-{n}" for n in range(1, 201)]
    assert [user for user in users if can_use(user, "holiday_theme")] == []


def test_a_half_rollout_excludes_the_boundary_account():
    assert can_use("user-96", "dark_mode") is False
    assert can_use("user-7", "dark_mode") is True


def test_active_features_lists_only_what_is_on():
    assert active_features("user-7") == ("csv_export", "dark_mode", "new_editor")
    assert active_features("user-1") == ("new_editor",)


def test_require_raises_for_a_feature_the_account_does_not_have():
    with pytest.raises(PermissionError):
        require("user-1", "holiday_theme")
    with pytest.raises(UnknownFlag):
        require("user-1", "nope")


def test_the_explanation_names_the_reason():
    assert why("user-7", "csv_export") == "csv_export: on (on the allow list)"
    assert why("user-13", "new_editor") == "new_editor: off (on the deny list)"
    assert why("user-96", "dark_mode") == "dark_mode: off (bucket 50, rollout 50%)"


def test_the_status_page_shows_rollouts_in_progress():
    assert status_page() == {"csv_export": 0, "dark_mode": 50, "holiday_theme": 0}


def test_a_registry_can_also_be_built_from_a_mapping():
    registry = Registry.from_mapping({"solo": {"percent": 100}})
    assert registry.names() == ["solo"]
    assert registry.is_on("solo", "anyone") is True
