import pytest

from possible_change import possible_change


CASES = [
    ([[1, 4, 2], -7], 0),
    ([[1, 5, 10, 25], 11], 4),
    ([[1, 5, 10, 25], 75], 121),
    ([[1, 5, 10, 25], 34], 18),
    ([[1, 5, 10], 34], 16),
    ([[1, 5, 10, 25], 140], 568),
    ([[1, 5, 10, 25, 50], 140], 786),
    ([[1, 5, 10, 25, 50, 100], 140], 817),
    ([[1, 3, 7, 42, 78], 140], 981),
    ([[3, 7, 42, 78], 140], 20),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_possible_change(args, expected):
    result = possible_change(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
