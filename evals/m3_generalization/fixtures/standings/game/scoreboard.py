"""League standings assembled from recorded results."""

from game.stats import SEASON_DEFAULTS, merge_stats, points


def standings(results):
    """results maps team -> recorded stats. Return [(team, points)] best first.

    Teams may have partial records; anything unrecorded counts as zero.
    """
    table = []
    for team, recorded in results.items():
        stats = merge_stats(SEASON_DEFAULTS, recorded)
        table.append((team, points(stats)))
    table.sort(key=lambda entry: (-entry[1], entry[0]))
    return table
