"""The fallback: walk every row and test it.

This is what the planner does when no index can help, and it is also the
reference the indexed paths are measured against - if a scan and an
index disagree about a condition, the index is wrong.
"""


def scan_ids(table, condition):
    """Ids of the rows matching ``condition``, in insertion order."""
    return [row_id for row_id, row in table.items() if condition.matches(row)]


def scan_rows(table, condition):
    """The rows matching ``condition``, in insertion order."""
    return [row for _, row in table.items() if condition.matches(row)]


def check_ids(table, condition, row_ids):
    """Keep the candidate ids whose row really matches, in row order.

    Candidates from an index arrive grouped by key, so the survivors are
    put back into the table's own order: a caller must not be able to
    tell which route the answer came by.
    """
    kept = []
    for row_id in row_ids:
        row = table.peek(row_id)
        if row is not None and condition.matches(row):
            kept.append(row_id)
    return table.in_order(kept)


def count_matching(table, condition):
    return len(scan_ids(table, condition))
