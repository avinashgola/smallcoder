"""run_command tool: run an allowlisted command inside the repository.

Safeguards: executable allowlist, no shell (argv exec only), shell
metacharacter rejection, timeout, output truncation, cwd pinned to the repo.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from smallcoder.agent.schemas import RunCommandArgs
from smallcoder.config import Settings
from smallcoder.tools.base import ToolResult, truncate_output

FORBIDDEN_TOKENS = {"&&", "||", ";", "|", ">", ">>", "<", "&", "`", "$("}


def run_argv(
    repo_root: Path, argv: list[str], timeout: int, max_chars: int
) -> tuple[int | None, str]:
    """Run argv in the repo without a shell. Returns (exit_code, combined output).

    exit_code is None on timeout.
    """
    try:
        proc = subprocess.run(
            argv,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"Command timed out after {timeout}s."
    except FileNotFoundError:
        return 127, f"Executable not found: {argv[0]}"
    combined = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return proc.returncode, truncate_output(combined.strip(), max_chars)


def run_command(repo_root: Path, args: RunCommandArgs, settings: Settings) -> ToolResult:
    try:
        argv = shlex.split(args.command)
    except ValueError as exc:
        return ToolResult(ok=False, output="", error=f"Cannot parse command: {exc}")
    if not argv:
        return ToolResult(ok=False, output="", error="Empty command.")

    bad = [tok for tok in argv if tok in FORBIDDEN_TOKENS or tok.startswith("$(")]
    if bad:
        return ToolResult(
            ok=False,
            output="",
            error=f"Shell operators are not supported: {' '.join(bad)}. Run one command at a time.",
        )

    executable = Path(argv[0]).name
    if executable not in settings.allowed_commands:
        allowed = ", ".join(settings.allowed_commands)
        return ToolResult(
            ok=False,
            output="",
            error=f"Command {executable!r} is not allowed. Allowed commands: {allowed}.",
        )

    exit_code, output = run_argv(
        repo_root, argv, timeout=settings.command_timeout, max_chars=settings.max_tool_output_chars
    )
    if exit_code is None:
        return ToolResult(ok=False, output="", error=output)
    status = f"exit code {exit_code}"
    body = output or "(no output)"
    return ToolResult(ok=exit_code == 0, output=f"[{status}]\n{body}",
                      error=None if exit_code == 0 else f"Command failed with {status}.\n{body}")
