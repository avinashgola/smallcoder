import pytest

from lis import lis


CASES = [
    ([[]], 0),
    ([[3]], 1),
    ([[10, 20, 11, 32, 22, 48, 43]], 4),
    ([[4, 2, 1]], 1),
    ([[5, 1, 3, 4, 7]], 4),
    ([[4, 1]], 1),
    ([[-1, 0, 2]], 3),
    ([[0, 2]], 2),
    ([[4, 1, 5, 3, 7, 6, 2]], 3),
    ([[10, 22, 9, 33, 21, 50, 41, 60, 80]], 6),
    ([[7, 10, 9, 2, 3, 8, 1]], 3),
    ([[9, 11, 2, 13, 7, 15]], 4),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_lis(args, expected):
    result = lis(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
