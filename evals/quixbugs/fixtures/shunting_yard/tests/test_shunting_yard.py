import pytest

from shunting_yard import shunting_yard


CASES = [
    ([[]], []),
    ([[30]], [30]),
    ([[10, "-", 5, "-", 2]], [10, 5, "-", 2, "-"]),
    ([[34, "-", 12, "/", 5]], [34, 12, 5, "/", "-"]),
    ([[4, "+", 9, "*", 9, "-", 10, "+", 13]], [4, 9, 9, "*", "+", 10, "-", 13, "+"]),
    ([[7, "*", 43, "-", 7, "+", 13, "/", 7]], [7, 43, "*", 7, "-", 13, 7, "/", "+"]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_shunting_yard(args, expected):
    result = shunting_yard(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
