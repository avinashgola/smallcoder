import pytest

from get_factors import get_factors


CASES = [
    ([1], []),
    ([100], [2, 2, 5, 5]),
    ([101], [101]),
    ([104], [2, 2, 2, 13]),
    ([2], [2]),
    ([3], [3]),
    ([17], [17]),
    ([63], [3, 3, 7]),
    ([74], [2, 37]),
    ([73], [73]),
    ([9837], [3, 3, 1093]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_get_factors(args, expected):
    result = get_factors(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
