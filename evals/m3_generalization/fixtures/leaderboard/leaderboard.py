"""Score tracking for a small game leaderboard."""


def top_scores(scores, n):
    """Return the n highest scores, best first."""
    ranked = sorted(scores)
    return ranked[:n]


def podium(players):
    """players maps name -> score. Return up to three names, best first."""
    ordered = sorted(players, key=lambda name: players[name], reverse=True)
    return ordered[:3]


def personal_best(history):
    """The player's highest score so far, or None with no games played."""
    if not history:
        return None
    return max(history)
