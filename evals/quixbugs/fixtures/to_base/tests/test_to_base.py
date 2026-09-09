import pytest

from to_base import to_base


CASES = [
    ([8227, 18], "1771"),
    ([73, 8], "111"),
    ([16, 19], "G"),
    ([31, 16], "1F"),
    ([41, 2], "101001"),
    ([44, 5], "134"),
    ([27, 23], "14"),
    ([56, 23], "2A"),
    ([8237, 24], "E75"),
    ([8237, 34], "749"),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_to_base(args, expected):
    result = to_base(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
