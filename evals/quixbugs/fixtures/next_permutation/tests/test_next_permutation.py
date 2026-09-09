import pytest

from next_permutation import next_permutation


CASES = [
    ([[3, 2, 4, 1]], [3, 4, 1, 2]),
    ([[3, 5, 6, 2, 1]], [3, 6, 1, 2, 5]),
    ([[3, 5, 6, 2]], [3, 6, 2, 5]),
    ([[4, 5, 1, 7, 9]], [4, 5, 1, 9, 7]),
    ([[4, 5, 8, 7, 1]], [4, 7, 1, 5, 8]),
    ([[9, 5, 2, 6, 1]], [9, 5, 6, 1, 2]),
    ([[44, 5, 1, 7, 9]], [44, 5, 1, 9, 7]),
    ([[3, 4, 5]], [3, 5, 4]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_next_permutation(args, expected):
    result = next_permutation(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
