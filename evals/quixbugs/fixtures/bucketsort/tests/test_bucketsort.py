import pytest

from bucketsort import bucketsort


CASES = [
    ([[], 14], []),
    ([[3, 11, 2, 9, 1, 5], 12], [1, 2, 3, 5, 9, 11]),
    ([[3, 2, 4, 2, 3, 5], 6], [2, 2, 3, 3, 4, 5]),
    ([[1, 3, 4, 6, 4, 2, 9, 1, 2, 9], 10], [1, 1, 2, 2, 3, 4, 4, 6, 9, 9]),
    ([[20, 19, 18, 17, 16, 15, 14, 13, 12, 11], 21], [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
    ([[20, 21, 22, 23, 24, 25, 26, 27, 28, 29], 30], [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]),
    ([[8, 5, 3, 1, 9, 6, 0, 7, 4, 2, 5], 10], [0, 1, 2, 3, 4, 5, 5, 6, 7, 8, 9]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_bucketsort(args, expected):
    result = bucketsort(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
