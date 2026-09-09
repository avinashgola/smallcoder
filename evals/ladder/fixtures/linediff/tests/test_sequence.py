from diffcore.hunks import change_ranges, group_hunks
from diffcore.lcs import common_subsequence, match_pairs
from diffcore.ops import DELETE, EQUAL, INSERT, counts, new_side, old_side
from diffcore.sequence import common_prefix, common_suffix, diff_lines

OLD = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
NEW = ["a", "B", "c", "d", "e", "f", "g", "h", "I", "j"]


def test_common_prefix():
    assert common_prefix(["a", "b", "c"], ["a", "b", "z"]) == 2
    assert common_prefix([], ["a"]) == 0
    assert common_prefix(["a"], ["z"]) == 0


def test_common_suffix_respects_the_skipped_prefix():
    assert common_suffix(["a", "b", "c"], ["z", "b", "c"]) == 2
    assert common_suffix(["a", "a"], ["a", "a"], skip=1) == 1


def test_common_subsequence():
    assert common_subsequence(list("abcde"), list("axcye")) == ["a", "c", "e"]
    assert common_subsequence([], list("abc")) == []


def test_match_pairs_prefers_early_matches():
    assert match_pairs(["x", "a"], ["a", "y"]) == [(1, 0)]


def test_diff_lines_reports_a_replacement():
    ops = diff_lines(["a", "b", "c"], ["a", "x", "c"])
    assert [op.tag for op in ops] == [EQUAL, DELETE, INSERT, EQUAL]
    assert [op.line for op in ops] == ["a", "b", "x", "c"]


def test_op_line_numbers_are_zero_based_per_side():
    ops = diff_lines(["a", "b"], ["a", "new", "b"])
    inserted = [op for op in ops if op.tag == INSERT][0]
    assert inserted.old is None
    assert inserted.new == 1
    assert ops[-1].old == 1 and ops[-1].new == 2


def test_ops_rebuild_both_sides():
    ops = diff_lines(OLD, NEW)
    assert old_side(ops) == OLD
    assert new_side(ops) == NEW


def test_ops_rebuild_both_sides_for_pure_insertion():
    old = ["a", "b"]
    new = ["a", "one", "two", "b"]
    ops = diff_lines(old, new)
    assert old_side(ops) == old
    assert new_side(ops) == new


def test_counts():
    assert counts(diff_lines(OLD, NEW)) == (2, 2)
    assert counts(diff_lines(["a"], ["a"])) == (0, 0)


def test_change_ranges_merge_when_they_overlap():
    ops = diff_lines(OLD, NEW)
    assert change_ranges(ops, 1) == [(0, 4), (8, 12)]
    assert change_ranges(ops, 5) == [(0, 12)]


def test_group_hunks_splits_distant_changes():
    ops = diff_lines(OLD, NEW)
    assert len(group_hunks(ops, 1)) == 2
    assert len(group_hunks(ops, 5)) == 1
    assert group_hunks(ops, 1)[0] == ops[0:4]


def test_group_hunks_of_an_unchanged_file_is_empty():
    assert group_hunks(diff_lines(OLD, OLD)) == []
