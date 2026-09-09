import pytest

from longest_common_subsequence import longest_common_subsequence


CASES = [
    (["headache", "pentadactyl"], "eadac"),
    (["daenarys", "targaryen"], "aary"),
    (["XMJYAUZ", "MZJAWXU"], "MJAU"),
    (["thisisatest", "testing123testing"], "tsitest"),
    (["1234", "1224533324"], "1234"),
    (["abcbdab", "bdcaba"], "bcba"),
    (["TATAGC", "TAGCAG"], "TAAG"),
    (["ABCBDAB", "BDCABA"], "BCBA"),
    (["ABCD", "XBCYDQ"], "BCD"),
    (["acbdegcedbg", "begcfeubk"], "begceb"),
]


@pytest.mark.parametrize("args,expected", CASES)
def test_longest_common_subsequence(args, expected):
    result = longest_common_subsequence(*args)
    if hasattr(result, "__next__"):
        result = list(result)  # generator; a str is iterable too, do not unwrap it
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-4, abs=1e-4)
    else:
        assert result == expected
