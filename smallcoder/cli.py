"""SmallCoder command-line interface."""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from smallcoder import __version__
from smallcoder.agent.runtime import AgentRuntime, RunResult
from smallcoder.config import load_settings
from smallcoder.models.base import ModelClientError
from smallcoder.models.ollama import OllamaClient
from smallcoder.observability.logger import TrajectoryLogger, load_run

app = typer.Typer(
    name="smallcoder",
    help="A coding-agent runtime optimized for small local LLMs.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
console = Console()


def _build_model(settings):
    if settings.provider != "ollama":
        raise typer.BadParameter(
            f"Unsupported provider {settings.provider!r}. Supported: ollama."
        )
    return OllamaClient(
        base_url=settings.base_url,
        model=settings.model,
        request_timeout=settings.request_timeout,
        structured_format=settings.structured_format,
        num_ctx=settings.context_limit,
        force_ipv4=settings.force_ipv4,
    )


def _print_result(result: RunResult) -> None:
    status = "[green]SUCCESS[/green]" if result.success else "[red]FAILED[/red]"
    if result.completion_mode == "runtime_rescued":
        status += " [yellow](completed by runtime verification, not by the model)[/yellow]"
    console.print()
    console.print(Panel.fit(f"{status}  (stop reason: {result.stop_reason})", title="Result"))

    if result.verification:
        table = Table(title="Verification")
        table.add_column("Check")
        table.add_column("Passed")
        table.add_column("Summary")
        for check in result.verification.checks:
            table.add_row(
                check.name,
                "[green]yes[/green]" if check.passed else "[red]no[/red]",
                check.summary,
            )
        console.print(table)

    if result.files_changed:
        console.print(f"[bold]Files changed:[/bold] {', '.join(result.files_changed)}")
    if result.diff:
        console.print(Syntax(result.diff, "diff", theme="ansi_dark", word_wrap=True))
    else:
        console.print("[dim]No changes in the working tree.[/dim]")
    if result.final_summary:
        console.print(f"[bold]Agent summary:[/bold] {result.final_summary}")

    stats = (
        f"steps={result.steps} model_calls={result.model_calls} "
        f"tokens_in={result.tokens_in} tokens_out={result.tokens_out} "
        f"structured_output_failures={result.structured_output_failures} "
        f"loop_detections={result.loop_detections} loop_interventions={result.loop_interventions} "
        f"file_not_found={result.file_not_found_errors} "
        f"path_suggestions={result.path_suggestions_emitted}"
        f"/{result.path_suggestions_followed} followed"
    )
    console.print(f"[dim]{stats}[/dim]")
    console.print(
        f"[dim]Trajectory: run id {result.run_id} (smallcoder inspect {result.run_id})[/dim]"
    )


@app.command()
def solve(
    repo: Path = typer.Option(..., "--repo", help="Path to the target git repository."),
    issue: str = typer.Option(..., "--issue", help="Natural-language issue to resolve."),
    model: str | None = typer.Option(None, "--model", help="Override OLLAMA_MODEL."),
    base_url: str | None = typer.Option(None, "--base-url", help="Override OLLAMA_BASE_URL."),
    max_steps: int | None = typer.Option(
        None, "--max-steps", help="Override SMALLCODER_MAX_STEPS."
    ),
    context_limit: int | None = typer.Option(
        None, "--context-limit", help="Override SMALLCODER_CONTEXT_LIMIT."
    ),
    test_command: str | None = typer.Option(
        None, "--test-command", help="Verification test command (default: auto-detect pytest)."
    ),
    loop_detector: bool | None = typer.Option(
        None,
        "--loop-detector/--no-loop-detector",
        help="Ablation flag: enable/disable loop detection (default: SMALLCODER_LOOP_DETECTOR).",
    ),
    stall_verification: bool | None = typer.Option(
        None,
        "--stall-verification/--no-stall-verification",
        help="Ablation flag: runtime-initiated verification when the model stalls.",
    ),
    path_feedback: bool | None = typer.Option(
        None,
        "--path-feedback/--no-path-feedback",
        help="Ablation flag: suggest real repository paths when a file reference fails.",
    ),
) -> None:
    """Resolve an issue in a local git repository autonomously."""
    load_dotenv()
    settings = load_settings(
        model=model,
        base_url=base_url,
        max_steps=max_steps,
        context_limit=context_limit,
        loop_detector=loop_detector,
        stall_verification=stall_verification,
        path_feedback=path_feedback,
    )
    try:
        client = _build_model(settings)
    except ModelClientError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    logger = TrajectoryLogger(settings.runs_dir)
    console.print(Panel.fit(issue, title="Issue"))
    console.print(
        f"[dim]repo={repo}  model={settings.model}  max_steps={settings.max_steps}  "
        f"run={logger.run_id}[/dim]"
    )

    def on_step(step: int, action, ok: bool) -> None:
        if action is None:
            console.print(f"  [red]step {step}: invalid model output[/red]")
            return
        mark = "[green]ok[/green]" if ok else "[red]failed[/red]"
        detail = (
            action.arguments.get("path")
            or action.arguments.get("query")
            or action.arguments.get("command")
            or ""
        )
        console.print(f"  step {step}: {action.action_type} {detail} ... {mark}")
        if action.thought_summary:
            console.print(f"    [dim]{action.thought_summary[:120]}[/dim]")

    try:
        runtime = AgentRuntime(
            repo_root=repo,
            issue=issue,
            model=client,
            settings=settings,
            logger=logger,
            test_command=test_command,
            on_step=on_step,
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    result = runtime.run()
    _print_result(result)
    raise typer.Exit(code=0 if result.success else 1)


@app.command()
def inspect(
    run_id: str = typer.Argument(..., help="Run id, as printed by `smallcoder solve`."),
) -> None:
    """Inspect a stored run trajectory."""
    load_dotenv()
    settings = load_settings()
    try:
        run = load_run(settings.runs_dir, run_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc

    meta = run["meta"]
    if meta:
        console.print(Panel.fit(meta.get("issue", "(no issue recorded)"), title=f"Run {run_id}"))
        console.print(f"[dim]repo={meta.get('repo')}  model={meta.get('model')}[/dim]")

    table = Table(title="Trajectory")
    table.add_column("#", justify="right")
    table.add_column("Event")
    table.add_column("Detail")
    for i, event in enumerate(run["events"], start=1):
        kind = event.get("event", "?")
        if kind == "step":
            action = event.get("action") or {}
            detail = f"{action.get('action_type')} {action.get('arguments')}"
            detail += " -> ok" if event.get("ok") else " -> FAILED"
        elif kind == "model_call":
            detail = (
                f"in={event.get('tokens_in')} out={event.get('tokens_out')} "
                f"{event.get('latency_ms')}ms ctx={event.get('context_chars')}ch"
            )
        elif kind == "verification":
            detail = f"passed={event.get('passed')}"
        else:
            detail = str(event.get("error") or event.get("message") or "")[:120]
        table.add_row(str(i), kind, detail[:160])
    console.print(table)

    result = run["result"]
    if result:
        console.print(
            f"[bold]Outcome:[/bold] success={result.get('success')} "
            f"stop_reason={result.get('stop_reason')} steps={result.get('steps')}"
        )


@app.command()
def version() -> None:
    """Print the SmallCoder version."""
    console.print(__version__)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
