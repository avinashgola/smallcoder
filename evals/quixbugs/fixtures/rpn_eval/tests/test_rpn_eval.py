import pytest

from rpn_eval import rpn_eval


CASES = [
    ([[3.0, 5.0, "+", 2.0, "/"]], 4.0),
    ([[2.0, 2.0, "+"]], 4.0),
    ([[7.0, 4.0, "+", 3.0, "-"]], 8.0),
    ([[1.0, 2.0, "*", 3.0, 4.0, "*", "+"]], 14.0),
    ([[5.0, 9.0, 2.0, "*", "+"]], 23.0),
    ([[5.0, 1.0, 2.0, "+", 4.0, "*", "+", 3.0, "-"]], 14.0),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_rpn_eval(args, expected):
    result = rpn_eval(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
