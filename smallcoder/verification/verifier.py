"""Deterministic verification: never trust the model's claim of success.

When the model requests `finish`, the runtime runs this pipeline:
  1. changes_present  - did the working tree actually change vs. the baseline?
  2. python_syntax    - do all edited .py files still compile?
  3. tests            - explicit --test-command, or auto-detected pytest.

Only if every applicable check passes is the run declared successful.
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

from pydantic import BaseModel

from smallcoder.config import Settings
from smallcoder.gitutils import RepoSnapshot, changed_since
from smallcoder.tools.run_command import run_argv


class CheckResult(BaseModel):
    name: str
    passed: bool
    exit_code: int | None = None
    summary: str = ""


class VerificationResult(BaseModel):
    passed: bool
    checks: list[CheckResult]

    def failure_summary(self) -> str:
        failed = [c for c in self.checks if not c.passed]
        if not failed:
            return "all checks passed"
        return "; ".join(f"{c.name}: {c.summary}" for c in failed)


def detect_test_command(repo_root: Path) -> list[str] | None:
    """Auto-detect a test command. V1: pytest if the repo has pytest-style tests."""
    has_tests = any(repo_root.glob("tests/test_*.py")) or any(
        repo_root.glob("test_*.py")
    ) or any(repo_root.glob("tests/**/test_*.py"))
    if has_tests:
        return [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]
    return None


def _tail_summary(output: str, max_chars: int = 300) -> str:
    lines = [line for line in output.strip().splitlines() if line.strip()]
    return " | ".join(lines[-3:])[:max_chars] if lines else "(no output)"


def verify(
    repo_root: Path,
    settings: Settings,
    baseline: RepoSnapshot,
    edited_files: list[str],
    test_command: str | None = None,
) -> VerificationResult:
    checks: list[CheckResult] = []

    changed = changed_since(repo_root, baseline)
    checks.append(
        CheckResult(
            name="changes_present",
            passed=bool(changed),
            summary=f"{len(changed)} file(s) changed" if changed else "no changes in working tree",
        )
    )

    edited_py = [f for f in edited_files if f.endswith(".py")]
    if edited_py:
        failures = []
        for rel in edited_py:
            file_path = repo_root / rel
            if not file_path.exists():
                continue
            try:
                compile(file_path.read_text(encoding="utf-8"), rel, "exec")
            except SyntaxError as exc:
                failures.append(f"{rel}:{exc.lineno}: {exc.msg}")
        checks.append(
            CheckResult(
                name="python_syntax",
                passed=not failures,
                summary="; ".join(failures) if failures else f"{len(edited_py)} file(s) compile",
            )
        )

    if test_command:
        argv = shlex.split(test_command)
        test_name = argv[0]
    else:
        argv = detect_test_command(repo_root) or []
        test_name = "pytest (auto-detected)"
    if argv:
        exit_code, output = run_argv(
            repo_root, argv, timeout=settings.command_timeout,
            max_chars=settings.max_tool_output_chars,
        )
        checks.append(
            CheckResult(
                name=test_name,
                passed=exit_code == 0,
                exit_code=exit_code,
                summary="timed out" if exit_code is None else _tail_summary(output),
            )
        )

    return VerificationResult(passed=all(c.passed for c in checks), checks=checks)
