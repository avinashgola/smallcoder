import pytest

from gcd import gcd


CASES = [
    ([17, 0], 17),
    ([13, 13], 13),
    ([37, 600], 1),
    ([20, 100], 20),
    ([624129, 2061517], 18913),
    ([3, 12], 3),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_gcd(args, expected):
    result = gcd(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
