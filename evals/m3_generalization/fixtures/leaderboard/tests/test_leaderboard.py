from leaderboard import personal_best, podium, top_scores


def test_top_scores_best_first():
    assert top_scores([300, 120, 950], 2) == [950, 300]


def test_top_scores_with_fewer_games_than_requested():
    assert top_scores([10, 40], 5) == [40, 10]


def test_podium():
    players = {"ana": 40, "bo": 90, "cy": 70, "dee": 10}
    assert podium(players) == ["bo", "cy", "ana"]


def test_personal_best():
    assert personal_best([12, 90, 45]) == 90
    assert personal_best([]) is None
