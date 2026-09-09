import pytest

from flatten import flatten


CASES = [
    ([[[1, [], [2, 3]], [[4]], 5]], [1, 2, 3, 4, 5]),
    ([[[], [], [], [], []]], []),
    ([[[], [], 1, [], 1, [], []]], [1, 1]),
    ([[1, 2, 3, [[4]]]], [1, 2, 3, 4]),
    ([[1, 4, 6]], [1, 4, 6]),
    ([["moe", "curly", "larry"]], ["moe", "curly", "larry"]),
    ([["a", "b", ["c"], ["d"], [["e"]]]], ["a", "b", "c", "d", "e"]),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_flatten(args, expected):
    result = flatten(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
