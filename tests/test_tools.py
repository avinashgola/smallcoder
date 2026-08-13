from pathlib import Path

from smallcoder.agent.schemas import (
    EditFileArgs,
    ReadFileArgs,
    RunCommandArgs,
    SearchCodeArgs,
)
from smallcoder.tools.base import truncate_output
from smallcoder.tools.edit_file import edit_file
from smallcoder.tools.read_file import read_file
from smallcoder.tools.run_command import run_command
from smallcoder.tools.search_code import search_code

# ------------------------------------------------------------------ read_file


def test_read_file_full(repo: Path):
    result = read_file(repo, ReadFileArgs(path="src/auth.py"))
    assert result.ok
    assert "def normalize" in result.output
    assert "    1|" in result.output


def test_read_file_range(repo: Path):
    result = read_file(repo, ReadFileArgs(path="src/auth.py", start_line=4, end_line=5))
    assert result.ok
    assert "validate_email" in result.output
    assert "normalize" not in result.output.split("\n", 1)[1]


def test_read_file_not_found(repo: Path):
    result = read_file(repo, ReadFileArgs(path="src/missing.py"))
    assert not result.ok
    assert "not found" in result.error.lower()


def test_read_file_blocks_traversal(repo: Path):
    result = read_file(repo, ReadFileArgs(path="../outside.txt"))
    assert not result.ok
    assert "escapes" in result.error


def test_read_file_blocks_absolute(repo: Path):
    result = read_file(repo, ReadFileArgs(path="/etc/passwd"))
    assert not result.ok
    assert "Absolute" in result.error


def test_read_file_blocks_git_dir(repo: Path):
    result = read_file(repo, ReadFileArgs(path=".git/config"))
    assert not result.ok
    assert ".git" in result.error


# ---------------------------------------------------------------- search_code


def test_search_finds_symbol(repo: Path):
    result = search_code(repo, SearchCodeArgs(query="validate_email"))
    assert result.ok
    assert "src/auth.py" in result.output


def test_search_no_matches(repo: Path):
    result = search_code(repo, SearchCodeArgs(query="zzz_does_not_exist"))
    assert result.ok
    assert "No matches" in result.output


def test_search_scoped_path_traversal_blocked(repo: Path):
    result = search_code(repo, SearchCodeArgs(query="x", path="../"))
    assert not result.ok


# ------------------------------------------------------------------ edit_file


def test_edit_unique_replace(repo: Path):
    result = edit_file(
        repo,
        EditFileArgs(
            path="src/auth.py",
            old_text="return email.strip()",
            new_text="return email.strip().lower()",
        ),
    )
    assert result.ok
    assert result.files_touched == ["src/auth.py"]
    assert "lower()" in (repo / "src/auth.py").read_text()


def test_edit_rejects_no_match(repo: Path):
    result = edit_file(
        repo, EditFileArgs(path="src/auth.py", old_text="not in file", new_text="x")
    )
    assert not result.ok
    assert "not found" in result.error


def test_edit_rejects_ambiguous_match(repo: Path):
    result = edit_file(
        repo, EditFileArgs(path="src/auth.py", old_text="email", new_text="address")
    )
    assert not result.ok
    assert "must be unique" in result.error


def test_edit_creates_new_file(repo: Path):
    result = edit_file(
        repo, EditFileArgs(path="src/new_module.py", old_text="", new_text="VALUE = 1\n")
    )
    assert result.ok
    assert (repo / "src/new_module.py").read_text() == "VALUE = 1\n"


def test_edit_create_refuses_existing_file(repo: Path):
    result = edit_file(repo, EditFileArgs(path="src/auth.py", old_text="", new_text="x"))
    assert not result.ok
    assert "already exists" in result.error


def test_edit_blocks_traversal(repo: Path):
    result = edit_file(
        repo, EditFileArgs(path="../evil.py", old_text="", new_text="import os")
    )
    assert not result.ok


def test_edit_blocks_git_dir(repo: Path):
    result = edit_file(
        repo, EditFileArgs(path=".git/hooks/pre-commit", old_text="", new_text="#!/bin/sh")
    )
    assert not result.ok


# ---------------------------------------------------------------- run_command


def test_run_command_allowed(repo: Path, settings):
    result = run_command(repo, RunCommandArgs(command="python3 -c 'print(40 + 2)'"), settings)
    assert result.ok
    assert "42" in result.output


def test_run_command_denies_unlisted_executable(repo: Path, settings):
    result = run_command(repo, RunCommandArgs(command="curl http://example.com"), settings)
    assert not result.ok
    assert "not allowed" in result.error


def test_run_command_denies_shell_operators(repo: Path, settings):
    result = run_command(repo, RunCommandArgs(command="python3 -V && rm -rf /"), settings)
    assert not result.ok
    assert "Shell operators" in result.error


def test_run_command_timeout(repo: Path, settings):
    fast = type(settings)(
        model=settings.model,
        runs_dir=settings.runs_dir,
        command_timeout=1,
        max_tool_output_chars=2000,
    )
    result = run_command(
        repo, RunCommandArgs(command="python3 -c 'import time; time.sleep(5)'"), fast
    )
    assert not result.ok
    assert "timed out" in result.error


def test_run_command_reports_nonzero_exit(repo: Path, settings):
    result = run_command(
        repo, RunCommandArgs(command="python3 -c 'raise SystemExit(3)'"), settings
    )
    assert not result.ok
    assert "exit code 3" in result.error


def test_run_command_truncates_output(repo: Path, settings):
    result = run_command(
        repo, RunCommandArgs(command="python3 -c 'print(\"a\" * 100000)'"), settings
    )
    assert result.ok
    assert len(result.output) < 5000
    assert "truncated" in result.output


# --------------------------------------------------------------------- shared


def test_truncate_output_keeps_head_and_tail():
    text = "HEAD" + "x" * 10000 + "TAIL"
    out = truncate_output(text, 1000)
    assert out.startswith("HEAD")
    assert out.endswith("TAIL")
    assert "truncated" in out
