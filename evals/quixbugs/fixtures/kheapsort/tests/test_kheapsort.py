import pytest

from kheapsort import kheapsort


CASES = [
    ([[1, 2, 3, 4, 5], 0], [1, 2, 3, 4, 5]),
    ([[3, 2, 1, 5, 4], 2], [1, 2, 3, 4, 5]),
    ([[5, 4, 3, 2, 1], 4], [1, 2, 3, 4, 5]),
    ([[3, 12, 5, 1, 6], 3], [1, 3, 5, 6, 12]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_kheapsort(args, expected):
    result = kheapsort(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
