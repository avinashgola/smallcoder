import pytest

from util.ids import group_name, is_group_ref, normalize_id, run_id, short
from util.sets import ordered_difference, ordered_intersection, ordered_unique
from util.tabular import render_table
from util.text import indent, joined, plural, truncate
from util.timing import StepClock, Stopwatch, format_seconds


def test_normalize_id():
    assert normalize_id("  Build.Step-1 ") == "build.step-1"
    with pytest.raises(ValueError):
        normalize_id("")
    with pytest.raises(ValueError):
        normalize_id("has space")


def test_group_refs():
    assert is_group_ref("@build")
    assert not is_group_ref("build")
    assert group_name("@Build") == "build"


def test_run_id_and_short():
    assert run_id("nightly", 7) == "nightly-0007"
    assert short("abcdefghijklmnop", 9) == "abc...nop"
    assert short("tiny", 9) == "tiny"


def test_ordered_set_helpers():
    assert ordered_unique(["b", "a", "b", "c"]) == ["b", "a", "c"]
    assert ordered_difference(["a", "b", "c"], {"b"}) == ["a", "c"]
    assert ordered_intersection(["a", "b", "c"], {"c", "a"}) == ["a", "c"]


def test_text_helpers():
    assert indent("a\nb") == "  a\n  b"
    assert truncate("abcdefg", 5) == "ab..."
    assert plural(1, "job") == "1 job"
    assert plural(2, "job") == "2 jobs"
    assert joined(["a", "b", "c"]) == "a, b and c"


def test_stopwatch_uses_the_injected_clock():
    clock = StepClock(start=10.0, step=2.5)
    watch = Stopwatch(clock).start()
    assert watch.stop() == 2.5


def test_format_seconds():
    assert format_seconds(0.25) == "250ms"
    assert format_seconds(3.0) == "3.0s"
    assert format_seconds(125.0) == "2m05s"


def test_render_table():
    table = render_table([("a", 1), ("bbbb", 22)], ("job", "n"))
    lines = table.splitlines()
    assert lines[0].startswith("job")
    assert lines[1].startswith("----")
    assert lines[2].startswith("a")
