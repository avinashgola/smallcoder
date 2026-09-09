import pytest

from powerset import powerset


CASES = [
    ([["a", "b", "c"]], [[], ["c"], ["b"], ["b", "c"], ["a"], ["a", "c"], ["a", "b"], ["a", "b", "c"]]),
    ([["a", "b"]], [[], ["b"], ["a"], ["a", "b"]]),
    ([["a"]], [[], ["a"]]),
    ([[]], [[]]),
    ([["x", "df", "z", "m"]], [[], ["m"], ["z"], ["z", "m"], ["df"], ["df", "m"], ["df", "z"], ["df", "z", "m"], ["x"], ["x", "m"], ["x", "z"], ["x", "z", "m"], ["x", "df"], ["x", "df", "m"], ["x", "df", "z"], ["x", "df", "z", "m"]]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_powerset(args, expected):
    result = powerset(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
