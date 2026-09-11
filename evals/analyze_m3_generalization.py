"""Preregistered analysis for the M3 generalization study (stdlib only).

Implements exactly the analysis frozen in
results/analysis/m3-generalization-preregistration.md:

  - validates the frozen 240-key plan and requires exactly one row per key;
  - joins rows to task specs and to trajectories by run_id;
  - GT-read definition (preregistered): a run counts as a ground-truth read
    iff its trajectory contains a successful (`ok: true`) `read_file` step
    whose `arguments.path` exactly equals an entry in the task's
    `ground_truth_files`;
  - emits a sanitized per-run mechanism file (whitelisted fields only — no
    observations, prompts, diffs, repository paths, or endpoint strings);
  - the task is the unit of generalization: per-task arm rates, paired B−A
    differences, and a 10,000-resample task-cluster bootstrap
    (seed 20260815, fresh RNG per model/outcome) give point estimates and
    95% percentile intervals, separately per model — never combined;
  - run-level Fisher exact tests are labelled descriptive only.

Identical inputs produce byte-identical output.

For archival/CI reproduction, ``--derived-input`` accepts the tracked,
sanitized mechanism rows and validates every non-derived field against the
raw benchmark rows.  This avoids requiring gitignored trajectories merely to
recompute an already-published analysis.  Omitting it retains the original
trajectory-extraction path used to create the sanitized artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from evals.analyze_rows import RowsError, fisher_exact_two_sided, load_rows, validate_rows
from evals.run_m3_generalization import build_plan

BOOTSTRAP_SEED = 20260815
BOOTSTRAP_RESAMPLES = 10_000
OUTCOMES = ("gt_read", "success")

DERIVED_FIELDS = (
    "run_id",
    "schedule_index",
    "model",
    "config",
    "arm",
    "task",
    "trial",
    "success",
    "gt_read",
    "file_not_found_errors",
    "path_suggestions_emitted",
    "path_suggestions_followed",
    "steps",
    "tokens_in",
    "tokens_out",
    "duration_s",
    "completion_mode",
)

METRIC_MEANS = (
    "file_not_found_errors",
    "path_suggestions_emitted",
    "path_suggestions_followed",
    "steps",
    "tokens_in",
    "tokens_out",
    "duration_s",
)


class AnalysisError(ValueError):
    pass


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text())
    rebuilt = build_plan(plan["tasks"])
    if plan.get("fingerprint") != rebuilt["fingerprint"]:
        raise AnalysisError("plan fingerprint does not match the frozen schedule")
    return plan


def check_rows_against_plan(plan: dict, rows: list[dict]) -> None:
    planned_entries = {
        (e["model"], e["config"], e["task"], e["trial"]): e
        for e in plan["entries"]
    }
    planned = set(planned_entries)
    seen: Counter = Counter((r["model"], r["config"], r["task"], r["trial"]) for r in rows)
    unknown = sorted(k for k in seen if k not in planned)
    if unknown:
        raise AnalysisError(f"rows contain {len(unknown)} unplanned key(s), e.g. {unknown[0]}")
    dupes = sorted(k for k, n in seen.items() if n > 1)
    if dupes:
        raise AnalysisError(f"{len(dupes)} duplicate planned key(s), e.g. {dupes[0]}")
    missing = sorted(planned - set(seen))
    if missing:
        raise AnalysisError(f"{len(missing)} planned run(s) missing, e.g. {missing[0]}")
    for row in rows:
        key = (row["model"], row["config"], row["task"], row["trial"])
        expected_index = planned_entries[key]["schedule_index"]
        if row.get("schedule_index") != expected_index:
            raise AnalysisError(
                f"schedule_index mismatch for {key}: "
                f"expected {expected_index}, got {row.get('schedule_index')}"
            )


def load_task_specs(tasks_dir: Path) -> dict[str, dict]:
    return {
        spec["id"]: spec
        for spec in (json.loads(p.read_text()) for p in sorted(tasks_dir.glob("*.json")))
    }


def gt_read_from_trajectory(trajectory_path: Path, gt_files: list[str]) -> bool:
    """Preregistered rule: successful read_file with path exactly in gt_files."""
    if not trajectory_path.is_file():
        raise AnalysisError(f"missing trajectory: {trajectory_path.name} "
                            f"(run {trajectory_path.parent.name})")
    targets = set(gt_files)
    try:
        for line in trajectory_path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event") != "step":
                continue
            action = record.get("action") or {}
            if action.get("action_type") != "read_file":
                continue
            if not record.get("ok"):
                continue
            if (action.get("arguments") or {}).get("path") in targets:
                return True
    except (json.JSONDecodeError, AttributeError) as exc:
        raise AnalysisError(
            f"malformed trajectory for run {trajectory_path.parent.name}: {exc}"
        ) from exc
    return False


def derive_mechanism_rows(rows: list[dict], specs: dict[str, dict], runs_dir: Path) -> list[dict]:
    derived = []
    for row in rows:
        spec = specs.get(row["task"])
        if spec is None:
            raise AnalysisError(f"no task spec for {row['task']}")
        trajectory = runs_dir / row["run_id"] / "trajectory.jsonl"
        record = {
            field: row.get(field)
            for field in DERIVED_FIELDS
            if field not in ("gt_read",)
        }
        record["gt_read"] = gt_read_from_trajectory(trajectory, spec["ground_truth_files"])
        derived.append(record)
    derived.sort(key=lambda r: r["schedule_index"])
    return derived


def load_derived_rows(path: Path) -> list[dict]:
    """Load a tracked sanitized mechanism artifact, rejecting schema drift."""
    if not path.is_file():
        raise AnalysisError(f"missing derived mechanism file: {path}")
    expected_fields = set(DERIVED_FIELDS)
    derived: list[dict] = []
    try:
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise AnalysisError(f"derived line {lineno}: expected a JSON object")
            fields = set(record)
            if fields != expected_fields:
                missing = sorted(expected_fields - fields)
                extra = sorted(fields - expected_fields)
                raise AnalysisError(
                    f"derived line {lineno}: field mismatch "
                    f"(missing={missing}, extra={extra})"
                )
            if not isinstance(record["gt_read"], bool):
                raise AnalysisError(f"derived line {lineno}: gt_read must be boolean")
            if not isinstance(record["schedule_index"], int):
                raise AnalysisError(f"derived line {lineno}: schedule_index must be integer")
            derived.append(record)
    except json.JSONDecodeError as exc:
        raise AnalysisError(
            f"derived line {exc.lineno}: malformed JSON ({exc.msg})"
        ) from exc
    if not derived:
        raise AnalysisError(f"derived mechanism file is empty: {path}")
    derived.sort(key=lambda r: r["schedule_index"])
    return derived


def validate_derived_rows(rows: list[dict], derived: list[dict]) -> None:
    """Bind tracked mechanism rows to raw rows; only ``gt_read`` may differ."""
    raw_by_index: dict[int, dict] = {}
    for row in rows:
        index = row.get("schedule_index")
        if not isinstance(index, int):
            raise AnalysisError(f"raw row has invalid schedule_index: {index!r}")
        if index in raw_by_index:
            raise AnalysisError(f"raw rows duplicate schedule_index {index}")
        raw_by_index[index] = row

    derived_by_index: dict[int, dict] = {}
    for record in derived:
        index = record["schedule_index"]
        if index in derived_by_index:
            raise AnalysisError(f"derived rows duplicate schedule_index {index}")
        derived_by_index[index] = record

    if set(derived_by_index) != set(raw_by_index):
        missing = sorted(set(raw_by_index) - set(derived_by_index))
        extra = sorted(set(derived_by_index) - set(raw_by_index))
        raise AnalysisError(
            "derived/raw schedule indexes differ "
            f"(missing={missing[:3]}, extra={extra[:3]})"
        )

    for index, raw in raw_by_index.items():
        record = derived_by_index[index]
        for field in DERIVED_FIELDS:
            if field == "gt_read":
                continue
            if record[field] != raw.get(field):
                raise AnalysisError(
                    f"derived field {field!r} disagrees with raw row at "
                    f"schedule_index {index}"
                )


def write_derived_rows(path: Path, derived: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in derived:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


def _percentile_interval(sorted_values: list[float]) -> tuple[float, float]:
    n = len(sorted_values)
    lo = sorted_values[int(0.025 * (n - 1))]
    hi = sorted_values[int(round(0.975 * (n - 1)))]
    return lo, hi


def cluster_bootstrap(task_diffs: list[float], resamples: int, seed: int) -> dict:
    """Resample tasks (the cluster unit) with replacement; never runs."""
    import random

    rng = random.Random(seed)
    n_tasks = len(task_diffs)
    point = sum(task_diffs) / n_tasks
    means = []
    for _ in range(resamples):
        draw = [task_diffs[rng.randrange(n_tasks)] for _ in range(n_tasks)]
        means.append(sum(draw) / n_tasks)
    means.sort()
    lo, hi = _percentile_interval(means)
    return {
        "point_estimate": round(point, 4),
        "ci95_low": round(lo, 4),
        "ci95_high": round(hi, 4),
        "resamples": resamples,
        "seed": seed,
        "unit": "task",
    }


def analyze(derived: list[dict], plan: dict, resamples: int) -> dict:
    models = plan["models"]
    tasks = plan["tasks"]
    arms = sorted(plan["arms"])  # ["A", "B"]
    ambiguous_tasks = ["invoices", "notify"]

    def cell(model, arm, task=None):
        return [
            r for r in derived
            if r["model"] == model and r["arm"] == arm and (task is None or r["task"] == task)
        ]

    result: dict = {
        "design": {
            "models": models,
            "tasks": tasks,
            "trials": plan["trials"],
            "arms": plan["arms"],
            "runs": len(derived),
            "ambiguous_candidate_tasks": ambiguous_tasks,
        },
        "per_model": {},
    }

    for model in models:
        model_block: dict = {"per_task": {}, "outcomes": {}, "metrics": {},
                             "completion_modes": {}, "fisher_descriptive": {}}
        for task in tasks:
            entry = {}
            for arm in arms:
                rows_at = cell(model, arm, task)
                entry[arm] = {
                    "n": len(rows_at),
                    "gt_read": sum(1 for r in rows_at if r["gt_read"]),
                    "solved": sum(1 for r in rows_at if r["success"]),
                    "file_not_found": sum(r["file_not_found_errors"] for r in rows_at),
                    "suggestions_emitted": sum(r["path_suggestions_emitted"] for r in rows_at),
                    "suggestions_followed": sum(r["path_suggestions_followed"] for r in rows_at),
                }
            entry["diff_gt_read"] = round(
                (entry["B"]["gt_read"] - entry["A"]["gt_read"]) / plan["trials"], 4
            )
            entry["diff_solved"] = round(
                (entry["B"]["solved"] - entry["A"]["solved"]) / plan["trials"], 4
            )
            model_block["per_task"][task] = entry

        for outcome in OUTCOMES:
            key = "gt_read" if outcome == "gt_read" else "solved"
            task_diffs = [model_block["per_task"][t][f"diff_{key}"] for t in tasks]
            totals = {}
            for arm in arms:
                rows_at = cell(model, arm)
                hit = sum(1 for r in rows_at
                          if (r["gt_read"] if outcome == "gt_read" else r["success"]))
                totals[arm] = {"hits": hit, "n": len(rows_at)}
            model_block["outcomes"][outcome] = {
                "arm_totals": totals,
                "per_task_paired_diffs": dict(
                    zip(tasks, task_diffs, strict=True)
                ),
                "cluster_bootstrap": cluster_bootstrap(task_diffs, resamples, BOOTSTRAP_SEED),
            }
            a, b = totals["A"], totals["B"]
            p = fisher_exact_two_sided(
                a["hits"], a["n"] - a["hits"], b["hits"], b["n"] - b["hits"]
            )
            model_block["fisher_descriptive"][outcome] = {
                "note": "descriptive only: treats clustered runs as observations",
                "arm_a": f"{a['hits']}/{a['n']}",
                "arm_b": f"{b['hits']}/{b['n']}",
                "p_two_sided": float(f"{p:.3g}"),
            }

        for arm in arms:
            rows_at = cell(model, arm)
            model_block["metrics"][arm] = {
                metric: round(sum(r[metric] for r in rows_at) / len(rows_at), 2)
                for metric in METRIC_MEANS
            }
            model_block["completion_modes"][arm] = dict(
                sorted(Counter(r["completion_mode"] or "none" for r in rows_at).items())
            )
        result["per_model"][model] = model_block
    return result


def render_markdown(result: dict) -> str:
    lines = ["# M3 generalization analysis (preregistered)", ""]
    design = result["design"]
    lines.append(
        f"{design['runs']} runs · models analysed separately (no combined headline) · "
        f"{len(design['tasks'])} tasks × {design['trials']} trials × 2 arms"
    )
    lines.append("")
    for model, block in result["per_model"].items():
        lines.append(f"## {model}")
        lines.append("")
        lines.append(
            "| task | A gt-read | B gt-read | A solved | B solved "
            "| B−A gt-read | B−A solved |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for task, entry in block["per_task"].items():
            flag = " *" if task in design["ambiguous_candidate_tasks"] else ""
            lines.append(
                f"| {task}{flag} | {entry['A']['gt_read']}/5 | {entry['B']['gt_read']}/5 "
                f"| {entry['A']['solved']}/5 | {entry['B']['solved']}/5 "
                f"| {entry['diff_gt_read']:+.1f} | {entry['diff_solved']:+.1f} |"
            )
        lines.append("")
        lines.append("`*` ambiguous-candidate task (duplicate basenames).")
        lines.append("")
        for outcome, data in block["outcomes"].items():
            boot = data["cluster_bootstrap"]
            a, b = data["arm_totals"]["A"], data["arm_totals"]["B"]
            fisher = block["fisher_descriptive"][outcome]
            lines.append(
                f"- **{outcome}**: arm A {a['hits']}/{a['n']}, arm B {b['hits']}/{b['n']}; "
                f"task-cluster bootstrap B−A = {boot['point_estimate']:+.3f} "
                f"(95% CI [{boot['ci95_low']:+.3f}, {boot['ci95_high']:+.3f}], "
                f"{boot['resamples']} resamples, seed {boot['seed']}, unit=task); "
                f"run-level Fisher p = {fisher['p_two_sided']} (descriptive only)"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.analyze_m3_generalization")
    parser.add_argument("--rows", default="results/benchmarks/m3_generalization/rows.jsonl")
    parser.add_argument("--plan", default="results/benchmarks/m3_generalization/plan.json")
    parser.add_argument("--tasks-dir", default="evals/m3_generalization/tasks")
    parser.add_argument("--runs-dir", default="results/runs")
    parser.add_argument(
        "--derived-input",
        default=None,
        help=(
            "Use a tracked sanitized mechanism JSONL instead of gitignored trajectories; "
            "all non-derived fields are validated against --rows"
        ),
    )
    parser.add_argument(
        "--derived-out", default="results/benchmarks/m3_generalization/mechanism.jsonl"
    )
    parser.add_argument("--resamples", type=int, default=BOOTSTRAP_RESAMPLES)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", dest="fmt")
    args = parser.parse_args(argv)

    try:
        plan = load_plan(Path(args.plan))
        rows = load_rows(args.rows)
        validate_rows(rows)
        check_rows_against_plan(plan, rows)
        if args.derived_input:
            derived = load_derived_rows(Path(args.derived_input))
            validate_derived_rows(rows, derived)
        else:
            specs = load_task_specs(Path(args.tasks_dir))
            derived = derive_mechanism_rows(rows, specs, Path(args.runs_dir))
    except (AnalysisError, RowsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_derived_rows(Path(args.derived_out), derived)

    result = analyze(derived, plan, args.resamples)
    if args.fmt == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
