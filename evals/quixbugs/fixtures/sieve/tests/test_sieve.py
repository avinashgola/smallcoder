import pytest

from sieve import sieve


CASES = [
    ([1], []),
    ([2], [2]),
    ([4], [2, 3]),
    ([7], [2, 3, 5, 7]),
    ([20], [2, 3, 5, 7, 11, 13, 17, 19]),
    ([50], [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_sieve(args, expected):
    result = sieve(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
