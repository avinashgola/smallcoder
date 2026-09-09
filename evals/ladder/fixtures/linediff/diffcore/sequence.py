"""Turn two sequences of lines into a flat list of ops."""

from .lcs import match_pairs
from .ops import delete, equal, insert


def common_prefix(a, b):
    """Number of identical lines at the start of both sequences."""
    limit = min(len(a), len(b))
    count = 0
    while count < limit and a[count] == b[count]:
        count += 1
    return count


def common_suffix(a, b, skip=0):
    """Identical trailing lines, ignoring the first `skip` lines of each."""
    limit = min(len(a), len(b)) - skip
    count = 0
    while count < limit and a[len(a) - 1 - count] == b[len(b) - 1 - count]:
        count += 1
    return count


def _diff_middle(old, new, old_base, new_base):
    """Ops for two sequences that share no prefix or suffix."""
    ops = []
    i = j = 0
    for match_i, match_j in match_pairs(old, new):
        while i < match_i:
            ops.append(delete(old[i], old_base + i))
            i += 1
        while j < match_j:
            ops.append(insert(new[j], new_base + j))
            j += 1
        ops.append(equal(old[i], old_base + i, new_base + j))
        i += 1
        j += 1
    while i < len(old):
        ops.append(delete(old[i], old_base + i))
        i += 1
    while j < len(new):
        ops.append(insert(new[j], new_base + j))
        j += 1
    return ops


def diff_lines(old, new):
    """Ops describing how to turn `old` into `new`.

    Identical leading and trailing lines are matched up directly; only the
    part in between is handed to the (much slower) subsequence search.
    """
    head = common_prefix(old, new)
    tail = common_suffix(old, new, head)
    ops = [equal(old[index], index, index) for index in range(head)]
    ops.extend(
        _diff_middle(
            old[head : len(old) - tail], new[head : len(new) - tail], head, head
        )
    )
    for offset in range(tail):
        i = len(old) - tail + offset
        j = len(new) - tail + offset
        ops.append(equal(old[i], i, j))
    return ops
