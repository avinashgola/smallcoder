"""Group a flat op list into hunks with surrounding context."""

from .ops import EQUAL

CONTEXT = 3


def change_ranges(ops, context=CONTEXT):
    """`(start, stop)` slices covering every change plus its context.

    Overlapping windows are merged so two nearby edits share one hunk.
    """
    if context < 0:
        raise ValueError("context must not be negative")
    ranges = []
    for index, op in enumerate(ops):
        if op.tag == EQUAL:
            continue
        start = max(0, index - context)
        stop = min(len(ops), index + context + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], stop)
        else:
            ranges.append((start, stop))
    return ranges


def group_hunks(ops, context=CONTEXT):
    """Split `ops` into the hunks a diff should actually print."""
    return [ops[start:stop] for start, stop in change_ranges(ops, context)]
