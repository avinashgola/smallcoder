import pytest

from kth import kth


CASES = [
    ([[1, 2, 3, 4, 5, 6, 7], 4], 5),
    ([[3, 6, 7, 1, 6, 3, 8, 9], 5], 7),
    ([[3, 6, 7, 1, 6, 3, 8, 9], 2], 3),
    ([[2, 6, 8, 3, 5, 7], 0], 2),
    ([[34, 25, 7, 1, 9], 4], 34),
    ([[45, 2, 6, 8, 42, 90, 322], 1], 6),
    ([[45, 2, 6, 8, 42, 90, 322], 6], 322),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_kth(args, expected):
    result = kth(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
