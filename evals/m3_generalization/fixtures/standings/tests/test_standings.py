from game.scoreboard import standings
from game.stats import SEASON_DEFAULTS, merge_stats, points


def test_points():
    assert points({"wins": 2, "losses": 1, "draws": 1}) == 7


def test_single_team():
    assert standings({"ants": {"wins": 2, "losses": 1}}) == [("ants", 6)]


def test_new_team_starts_from_zero():
    table = standings({"ants": {"wins": 2}, "bees": {}})
    assert table == [("ants", 6), ("bees", 0)]


def test_merge_does_not_change_the_defaults():
    merge_stats(SEASON_DEFAULTS, {"wins": 5})
    assert SEASON_DEFAULTS == {"wins": 0, "losses": 0, "draws": 0}
