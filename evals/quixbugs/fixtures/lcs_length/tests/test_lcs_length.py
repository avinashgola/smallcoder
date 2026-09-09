import pytest

from lcs_length import lcs_length


CASES = [
    (["witch", "sandwich"], 2),
    (["meow", "homeowner"], 4),
    (["fun", ""], 0),
    (["fun", "function"], 3),
    (["cyborg", "cyber"], 3),
    (["physics", "physics"], 7),
    (["space age", "pace a"], 6),
    (["flippy", "floppy"], 3),
    (["acbdegcedbg", "begcfeubk"], 3),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_lcs_length(args, expected):
    result = lcs_length(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
