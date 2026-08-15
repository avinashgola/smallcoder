"""Round-robin schedule generation."""


def pairings(teams):
    """All unique matchups, each pair exactly once."""
    return [(a, b) for i, a in enumerate(teams) for b in teams[i + 1:]]
