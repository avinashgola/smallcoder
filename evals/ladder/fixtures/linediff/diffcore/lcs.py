"""Longest common subsequence, used to line the two sides up."""


def lcs_table(a, b):
    """Table where `table[i][j]` is the LCS length of `a[i:]` and `b[j:]`."""
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        row = table[i]
        below = table[i + 1]
        for j in range(len(b) - 1, -1, -1):
            if a[i] == b[j]:
                row[j] = below[j + 1] + 1
            else:
                row[j] = max(below[j], row[j + 1])
    return table


def match_pairs(a, b):
    """Index pairs `(i, j)` where `a[i]` is matched with `b[j]`.

    Walking the table from the front keeps matches as early as possible,
    which reads better than an equally long match found later on.
    """
    table = lcs_table(a, b)
    pairs = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            pairs.append((i, j))
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def common_subsequence(a, b):
    """The longest sequence of items that appears in both, in order."""
    return [a[i] for i, _ in match_pairs(a, b)]
