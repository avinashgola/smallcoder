"""Recompute benchmark metrics from a tracked rows.jsonl file (stdlib only).

Every ablation sweep appends one JSON row per run to a rows.jsonl file under
results/benchmarks/. This tool re-derives the row-level numbers reported in
results/baseline/ from those tracked rows alone, so the reported tables can be
checked without access to the (gitignored) raw trajectories.

Usage:
  python -m evals.analyze_rows results/benchmarks/m3/rows.jsonl
  python -m evals.analyze_rows results/benchmarks/heldout/rows.jsonl \
      --dedupe keep-last --expect-cell-size 24 --format json

What it reproduces from rows.jsonl:
  - cell sizes, success counts, and solve rates per (model, config)
  - per-task solve counts per cell
  - completion-mode counts (model_initiated vs runtime_rescued)
  - per-cell means for the numeric metrics present in the rows (steps, tokens,
    duration, file-not-found errors, path-suggestion counters, ...)
  - two-sided Fisher exact p-values on solve rate when exactly two configs
    are present (per model and combined)

What it cannot reproduce (documented limitation): ground-truth-file *read*
rates, the suggestion->read->solve causal chain, and any per-step evidence.
Those come from trajectory.jsonl files under results/runs/, which are
gitignored; the reports in results/baseline/ state when a claim rests on them.

Duplicate (model, config, task, trial) keys are always reported. The default
policy is to fail on them; --dedupe keep-first / keep-last resolves them
deterministically by file order (e.g. the held-out sweep contains one
documented orphan row from an aborted cell whose re-run was appended later, so
--dedupe keep-last reproduces the published figures).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict

REQUIRED_FIELDS = ("run_id", "success", "stop_reason", "task", "trial", "model", "config")

# Means are computed for whichever of these a row actually carries; sweeps
# recorded before a counter existed simply omit it (reported as n_present).
NUMERIC_METRICS = (
    "steps",
    "model_calls",
    "tokens_in",
    "tokens_out",
    "duration_s",
    "structured_output_failures",
    "loop_detections",
    "loop_interventions",
    "stall_checks",
    "file_not_found_errors",
    "path_suggestions_emitted",
    "path_suggestions_followed",
    # Generic-loop control study. Absent from earlier sweeps, which is why
    # summarize() means over rows that carry a key rather than defaulting to 0:
    # a written zero would read as a measured zero.
    "claimed_success",
    "verified_final",
    "verified_checkpoint",
    "verified_ever",
    "overclaim",
    "silent_success",
    "delivered_success",
    "tampered",
    "commands_run",
    "edits_ok",
    "edits_failed",
    "peak_context_chars",
    "chars_sent_total",
    "n_messages_final",
    "model_latency_ms_total",
)


class RowsError(ValueError):
    """Malformed or inconsistent rows input; message says line and reason."""


def load_rows(path: str) -> list[dict]:
    rows: list[dict] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RowsError(f"line {lineno}: invalid JSON ({exc.msg})") from exc
                if not isinstance(row, dict):
                    raise RowsError(f"line {lineno}: expected a JSON object")
                row["_line"] = lineno
                rows.append(row)
    except OSError as exc:
        raise RowsError(f"cannot read {path}: {exc.strerror}") from exc
    if not rows:
        raise RowsError(f"{path} contains no rows")
    return rows


def validate_rows(rows: list[dict]) -> None:
    for row in rows:
        lineno = row["_line"]
        missing = [f for f in REQUIRED_FIELDS if f not in row]
        if missing:
            raise RowsError(f"line {lineno}: missing required field(s): {', '.join(missing)}")
        if not isinstance(row["success"], bool):
            raise RowsError(f"line {lineno}: 'success' must be a boolean")
        if not isinstance(row["trial"], int):
            raise RowsError(f"line {lineno}: 'trial' must be an integer")
        for field in ("task", "model", "config", "run_id", "stop_reason"):
            if not isinstance(row[field], str) or not row[field]:
                raise RowsError(f"line {lineno}: '{field}' must be a non-empty string")
        for metric in NUMERIC_METRICS:
            if metric in row and not isinstance(row[metric], int | float):
                raise RowsError(f"line {lineno}: '{metric}' must be numeric")


def row_key(row: dict) -> tuple[str, str, str, int]:
    return (row["model"], row["config"], row["task"], row["trial"])


def find_duplicates(rows: list[dict]) -> dict[tuple, list[int]]:
    """Map each duplicated (model, config, task, trial) key to its line numbers."""
    lines_by_key: dict[tuple, list[int]] = defaultdict(list)
    for row in rows:
        lines_by_key[row_key(row)].append(row["_line"])
    return {k: v for k, v in lines_by_key.items() if len(v) > 1}


def dedupe(rows: list[dict], policy: str) -> list[dict]:
    if policy == "error":
        dups = find_duplicates(rows)
        if dups:
            parts = [
                f"{'/'.join(map(str, key))} on lines {', '.join(map(str, lines))}"
                for key, lines in sorted(dups.items())
            ]
            raise RowsError(
                "duplicate model/config/task/trial keys: "
                + "; ".join(parts)
                + " (resolve with --dedupe keep-first or keep-last)"
            )
        return rows
    kept: dict[tuple, dict] = {}
    for row in rows:
        key = row_key(row)
        if policy == "keep-last" or key not in kept:
            kept[key] = row
    return sorted(kept.values(), key=lambda r: r["_line"])


def check_cell_sizes(rows: list[dict], expected: int) -> None:
    counts = Counter((r["model"], r["config"]) for r in rows)
    bad = {cell: n for cell, n in counts.items() if n != expected}
    if bad:
        parts = [f"{model}/{config}: {n}" for (model, config), n in sorted(bad.items())]
        raise RowsError(
            f"expected {expected} rows per model/config cell, got: " + "; ".join(parts)
        )


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 2)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for the 2x2 table [[a, b], [c, d]].

    Sums the probabilities of all tables with the same margins whose point
    probability does not exceed the observed table's (standard definition).
    """
    row1, row2, col1 = a + b, c + d, a + c
    n = row1 + row2

    def p_table(x: int) -> float:
        return (
            math.comb(row1, x)
            * math.comb(row2, col1 - x)
            / math.comb(n, col1)
        )

    observed = p_table(a)
    total = 0.0
    for x in range(max(0, col1 - row2), min(row1, col1) + 1):
        p = p_table(x)
        if p <= observed * (1 + 1e-9):
            total += p
    return min(total, 1.0)


def summarize(rows: list[dict]) -> dict:
    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        cells[(row["model"], row["config"])].append(row)

    cell_summaries = []
    for (model, config), cell_rows in sorted(cells.items()):
        successes = sum(1 for r in cell_rows if r["success"])
        metrics = {}
        for metric in NUMERIC_METRICS:
            values = [r[metric] for r in cell_rows if metric in r]
            if values:
                metrics[metric] = {"mean": _mean(values), "n_present": len(values)}
        per_task = {}
        for task in sorted({r["task"] for r in cell_rows}):
            task_rows = [r for r in cell_rows if r["task"] == task]
            per_task[task] = {
                "n": len(task_rows),
                "solved": sum(1 for r in task_rows if r["success"]),
            }
        completion_modes = dict(
            sorted(Counter(r.get("completion_mode") or "unrecorded" for r in cell_rows).items())
        )
        cell_summaries.append(
            {
                "model": model,
                "config": config,
                "n": len(cell_rows),
                "solved": successes,
                "solve_rate": round(successes / len(cell_rows), 3),
                "completion_modes": completion_modes,
                "metrics": metrics,
                "per_task": per_task,
            }
        )

    summary = {
        "rows": len(rows),
        "models": sorted({r["model"] for r in rows}),
        "configs": sorted({r["config"] for r in rows}),
        "tasks": sorted({r["task"] for r in rows}),
        "cells": cell_summaries,
    }

    configs = summary["configs"]
    if len(configs) == 2:
        comparisons = []
        groups = [*summary["models"], None]  # None = combined
        for model in groups:
            arms = []
            for config in configs:
                arm_rows = [
                    r
                    for r in rows
                    if r["config"] == config and (model is None or r["model"] == model)
                ]
                arms.append((sum(1 for r in arm_rows if r["success"]), len(arm_rows)))
            (s1, n1), (s2, n2) = arms
            if n1 == 0 or n2 == 0:
                continue
            comparisons.append(
                {
                    "model": model or "combined",
                    "config_a": configs[0],
                    "config_b": configs[1],
                    "solved_a": f"{s1}/{n1}",
                    "solved_b": f"{s2}/{n2}",
                    "fisher_two_sided_p": float(
                        f"{fisher_exact_two_sided(s1, n1 - s1, s2, n2 - s2):.3g}"
                    ),
                }
            )
        summary["solve_rate_comparisons"] = comparisons

    return summary


def render_markdown(summary: dict, source: str, duplicates: dict[tuple, list[int]]) -> str:
    lines = [
        f"# Benchmark rows summary: `{source}`",
        "",
        f"{summary['rows']} rows · models: {', '.join(summary['models'])} · "
        f"configs: {', '.join(summary['configs'])} · {len(summary['tasks'])} tasks",
        "",
    ]
    if duplicates:
        lines.append("**Duplicate keys resolved by dedupe policy:**")
        for key, dup_lines in sorted(duplicates.items()):
            lines.append(f"- `{'/'.join(map(str, key))}` on lines {', '.join(map(str, dup_lines))}")
        lines.append("")

    lines.append("## Cells")
    lines.append("")
    metric_names = sorted({m for c in summary["cells"] for m in c["metrics"]})
    header = ["model", "config", "n", "solved", "rate"] + [f"mean {m}" for m in metric_names]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + " --- |" * len(header))
    for cell in summary["cells"]:
        row = [
            cell["model"],
            cell["config"],
            str(cell["n"]),
            str(cell["solved"]),
            f"{cell['solve_rate']:.0%}",
        ]
        for m in metric_names:
            entry = cell["metrics"].get(m)
            row.append(f"{entry['mean']}" if entry else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## Completion modes")
    lines.append("")
    for cell in summary["cells"]:
        modes = ", ".join(f"{k}: {v}" for k, v in cell["completion_modes"].items())
        lines.append(f"- {cell['model']} / {cell['config']}: {modes}")
    lines.append("")

    lines.append("## Per-task solves")
    lines.append("")
    tasks = summary["tasks"]
    cell_headers = " | ".join(f"{c['model']} / {c['config']}" for c in summary["cells"])
    lines.append(f"| task | {cell_headers} |")
    lines.append("|" + " --- |" * (len(summary["cells"]) + 1))
    for task in tasks:
        row = [task]
        for cell in summary["cells"]:
            entry = cell["per_task"].get(task)
            row.append(f"{entry['solved']}/{entry['n']}" if entry else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    if "solve_rate_comparisons" in summary:
        lines.append("## Solve-rate comparison (Fisher exact, two-sided)")
        lines.append("")
        lines.append("| model | " + summary["solve_rate_comparisons"][0]["config_a"]
                     + " | " + summary["solve_rate_comparisons"][0]["config_b"] + " | p |")
        lines.append("| --- | --- | --- | --- |")
        for comp in summary["solve_rate_comparisons"]:
            lines.append(
                f"| {comp['model']} | {comp['solved_a']} | {comp['solved_b']} "
                f"| {comp['fisher_two_sided_p']} |"
            )
        lines.append("")

    lines.append(
        "*Derived from rows.jsonl only. Ground-truth-file read rates and "
        "suggestion causal chains require the gitignored trajectories and are "
        "not reproducible from this file.*"
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m evals.analyze_rows",
        description="Recompute benchmark metrics from a tracked rows.jsonl file.",
    )
    parser.add_argument("rows", help="Path to a rows.jsonl file")
    parser.add_argument(
        "--dedupe",
        choices=["error", "keep-first", "keep-last"],
        default="error",
        help="Policy for duplicate model/config/task/trial keys (default: fail).",
    )
    parser.add_argument(
        "--expect-cell-size",
        type=int,
        default=None,
        help="Fail unless every model/config cell has exactly this many rows (after dedupe).",
    )
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", dest="fmt"
    )
    args = parser.parse_args(argv)

    try:
        rows = load_rows(args.rows)
        validate_rows(rows)
        duplicates = find_duplicates(rows)
        rows = dedupe(rows, args.dedupe)
        if args.expect_cell_size is not None:
            check_cell_sizes(rows, args.expect_cell_size)
    except RowsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary = summarize(rows)
    if args.fmt == "json":
        summary["duplicates_resolved"] = [
            {"key": "/".join(map(str, key)), "lines": lines}
            for key, lines in sorted(duplicates.items())
        ]
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary, args.rows, duplicates), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
