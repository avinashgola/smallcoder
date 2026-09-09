import pytest

from max_sublist_sum import max_sublist_sum


CASES = [
    ([[4, -5, 2, 1, -1, 3]], 5),
    ([[0, -1, 2, -1, 3, -1, 0]], 4),
    ([[3, 4, 5]], 12),
    ([[4, -2, -8, 5, -2, 7, 7, 2, -6, 5]], 19),
    ([[-4, -4, -5]], 0),
    ([[-2, 1, -3, 4, -1, 2, 1, -5, 4]], 6),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_max_sublist_sum(args, expected):
    result = max_sublist_sum(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
