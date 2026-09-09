import pytest

from next_palindrome import next_palindrome


CASES = [
    ([[1, 4, 9, 4, 1]], [1, 5, 0, 5, 1]),
    ([[1, 3, 1]], [1, 4, 1]),
    ([[4, 7, 2, 5, 5, 2, 7, 4]], [4, 7, 2, 6, 6, 2, 7, 4]),
    ([[4, 7, 2, 5, 2, 7, 4]], [4, 7, 2, 6, 2, 7, 4]),
    ([[9, 9, 9]], [1, 0, 0, 1]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_next_palindrome(args, expected):
    result = next_palindrome(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
