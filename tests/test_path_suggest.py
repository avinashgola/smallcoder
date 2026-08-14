"""Tests for Milestone 3 deterministic path-resolution feedback."""

from __future__ import annotations

from pathlib import Path

from smallcoder.agent.schemas import EditFileArgs, ReadFileArgs
from smallcoder.config import Settings
from smallcoder.tools.edit_file import edit_file
from smallcoder.tools.path_suggest import (
    not_found_message,
    repo_files,
    suggest_paths,
)
from smallcoder.tools.read_file import read_file
from tests.conftest import make_git_repo

# ------------------------------------------------------------- suggest_paths


def test_exact_basename_match():
    assert suggest_paths("src/tempconv.py", ["tempconv.py", "tests/test_tempconv.py"]) == [
        "tempconv.py"
    ]


def test_unique_suffix_match():
    assert suggest_paths("src/utils/parser.py", ["utils/parser.py", "conftest.py"]) == [
        "utils/parser.py"
    ]


def test_ambiguous_basename_returns_all_candidates():
    got = suggest_paths("parser.py", ["src/parser.py", "tests/parser.py"])
    assert got == ["src/parser.py", "tests/parser.py"]


def test_suffix_disambiguates_between_same_basename():
    # Two files named parser.py, but the request's longer suffix matches one.
    got = suggest_paths("a/utils/parser.py", ["utils/parser.py", "tests/parser.py"])
    assert got == ["utils/parser.py"]


def test_no_candidate_returns_empty():
    assert suggest_paths("src/missing.py", ["tempconv.py", "conftest.py"]) == []


def test_case_insensitive_fallback():
    assert suggest_paths("src/TempConv.py", ["tempconv.py"]) == ["tempconv.py"]


def test_exact_case_wins_over_insensitive():
    got = suggest_paths("src/tempconv.py", ["tempconv.py", "TempConv.py"])
    assert got == ["tempconv.py"]


def test_never_suggests_the_requested_path_itself():
    assert suggest_paths("tempconv.py", ["tempconv.py"]) == []


def test_empty_request_is_safe():
    assert suggest_paths("", ["a.py"]) == []
    assert suggest_paths("   ", ["a.py"]) == []


def test_message_formatting_single_and_multiple():
    assert "Did you mean:\n- tempconv.py" in not_found_message("src/tempconv.py", ["tempconv.py"])
    multi = not_found_message("parser.py", ["src/parser.py", "tests/parser.py"])
    assert "Possible matches:" in multi
    assert "- src/parser.py" in multi and "- tests/parser.py" in multi
    assert not_found_message("x.py", []) == "File not found: x.py"


# ------------------------------------------------------------------ repo_files


def test_repo_files_excludes_git_and_caches(tmp_path: Path):
    repo = make_git_repo(tmp_path / "r", {"app.py": "x=1\n", "pkg/mod.py": "y=2\n"})
    (repo / "__pycache__").mkdir()
    (repo / "__pycache__" / "junk.pyc").write_text("junk")
    files = repo_files(repo)
    assert "app.py" in files and "pkg/mod.py" in files
    assert not any(f.startswith(".git") for f in files)
    assert not any("__pycache__" in f for f in files)


# ------------------------------------------------------------- read_file wiring


def _repo(tmp_path: Path) -> Path:
    return make_git_repo(
        tmp_path / "r",
        {"tempconv.py": "def f():\n    return 1\n", "tests/test_tempconv.py": "x = 1\n"},
    )


def test_read_file_suggests_real_path(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path="src/tempconv.py"), path_feedback=True)
    assert not result.ok
    assert result.file_not_found
    assert result.path_suggestions == ["tempconv.py"]
    assert "Did you mean:" in result.error
    assert "tempconv.py" in result.error


def test_read_file_without_flag_keeps_plain_error(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path="src/tempconv.py"), path_feedback=False)
    assert not result.ok
    assert result.file_not_found  # still counted
    assert result.path_suggestions == []
    assert result.error == "File not found: src/tempconv.py"


def test_read_file_no_candidate_plain_error(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path="src/nothing.py"), path_feedback=True)
    assert result.error == "File not found: src/nothing.py"
    assert result.path_suggestions == []


def test_read_file_valid_path_unchanged(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path="tempconv.py"), path_feedback=True)
    assert result.ok
    assert not result.file_not_found
    assert "def f()" in result.output


# ------------------------------------------------------------- edit_file wiring


def test_edit_file_suggests_and_changes_nothing(tmp_path: Path):
    repo = _repo(tmp_path)
    before = (repo / "tempconv.py").read_text()
    result = edit_file(
        repo,
        EditFileArgs(path="src/tempconv.py", old_text="return 1", new_text="return 2"),
        path_feedback=True,
    )
    assert not result.ok
    assert result.path_suggestions == ["tempconv.py"]
    assert "Did you mean:" in result.error
    assert result.files_touched == []
    assert (repo / "tempconv.py").read_text() == before  # nothing modified
    assert not (repo / "src").exists()  # no silent redirect or creation


def test_edit_file_without_flag_keeps_plain_error(tmp_path: Path):
    result = edit_file(
        _repo(tmp_path),
        EditFileArgs(path="src/tempconv.py", old_text="return 1", new_text="return 2"),
        path_feedback=False,
    )
    assert result.error == "File not found: src/tempconv.py"


# ----------------------------------------------------------------- sandbox


def test_traversal_gets_no_suggestion(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path="../tempconv.py"), path_feedback=True)
    assert not result.ok
    assert "escapes the repository" in result.error
    assert result.path_suggestions == []
    assert "Did you mean" not in result.error


def test_absolute_path_gets_no_suggestion(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path="/etc/tempconv.py"), path_feedback=True)
    assert "Absolute paths are not allowed" in result.error
    assert result.path_suggestions == []


def test_git_path_gets_no_suggestion(tmp_path: Path):
    result = read_file(_repo(tmp_path), ReadFileArgs(path=".git/config"), path_feedback=True)
    assert ".git" in result.error
    assert result.path_suggestions == []


def test_suggestions_never_leave_the_repository(tmp_path: Path):
    outside = tmp_path / "outside.py"
    outside.write_text("secret\n")
    repo = make_git_repo(tmp_path / "r", {"inside.py": "x=1\n"})
    assert suggest_paths("outside.py", repo_files(repo)) == []


# ------------------------------------------------------------------- config


def test_config_env_parsing(monkeypatch):
    from smallcoder.config import load_settings

    monkeypatch.delenv("SMALLCODER_PATH_FEEDBACK", raising=False)
    assert load_settings().path_feedback is True
    monkeypatch.setenv("SMALLCODER_PATH_FEEDBACK", "0")
    assert load_settings().path_feedback is False


# --------------------------------------------------------- runtime counters


def test_runtime_counts_and_attributes_suggestions(tmp_path: Path):
    from smallcoder.agent.runtime import AgentRuntime
    from smallcoder.models.mock import MockModelClient
    from smallcoder.observability.logger import TrajectoryLogger

    repo = _repo(tmp_path)
    settings = Settings(
        model="mock", runs_dir=tmp_path / "runs", max_steps=4,
        path_feedback=True, stall_verification=False,
    )
    model = MockModelClient(
        [
            {"action_type": "read_file", "arguments": {"path": "src/tempconv.py"}},  # fails
            {"action_type": "read_file", "arguments": {"path": "tempconv.py"}},      # follows
            {"action_type": "read_file", "arguments": {"path": "src/tempconv.py"}},  # fails
            {"action_type": "read_file", "arguments": {"path": "tests/test_tempconv.py"}},  # not
        ]
    )
    runtime = AgentRuntime(
        repo_root=repo, issue="x", model=model, settings=settings,
        logger=TrajectoryLogger(settings.runs_dir),
    )
    result = runtime.run()
    assert result.file_not_found_errors == 2
    assert result.path_suggestions_emitted == 2
    assert result.path_suggestions_followed == 1  # only the direct retry counts
