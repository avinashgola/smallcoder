"""Per-team stat blocks and point arithmetic."""

SEASON_DEFAULTS = {"wins": 0, "losses": 0, "draws": 0}


def merge_stats(base, extra):
    """Merge recorded results over a base stat block and return the result."""
    base.update(extra)
    return base


def points(stats):
    """League points: three per win, one per draw."""
    return stats["wins"] * 3 + stats["draws"]
