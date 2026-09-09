"""Line-oriented diffing.

`sequence.diff_lines` is the entry point: it turns two lists of lines into a
flat list of ops, which `hunks` groups and the `render` package formats.
"""

from .hunks import CONTEXT, change_ranges, group_hunks
from .lcs import common_subsequence, match_pairs
from .ops import DELETE, EQUAL, INSERT, counts, has_changes, new_side, old_side
from .sequence import common_prefix, common_suffix, diff_lines

__all__ = [
    "CONTEXT",
    "DELETE",
    "EQUAL",
    "INSERT",
    "change_ranges",
    "common_prefix",
    "common_subsequence",
    "common_suffix",
    "counts",
    "diff_lines",
    "group_hunks",
    "has_changes",
    "match_pairs",
    "new_side",
    "old_side",
]
