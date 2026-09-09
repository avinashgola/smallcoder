import pytest

from pascal import pascal


CASES = [
    ([1], [[1]]),
    ([2], [[1], [1, 1]]),
    ([3], [[1], [1, 1], [1, 2, 1]]),
    ([4], [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1]]),
    ([5], [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_pascal(args, expected):
    result = pascal(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
