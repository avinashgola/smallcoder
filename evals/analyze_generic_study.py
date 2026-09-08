"""Preregistered analysis for the generic agent-loop control study (stdlib only).

Implements exactly the plan frozen in
results/analysis/generic-loop-preregistration.md:

  - validates the frozen 360-key plan and requires exactly one row per key;
  - the task is the unit of generalization: 12 clusters, per model, NEVER
    pooled, with paired per-task differences and a task-cluster bootstrap
    reusing ``cluster_bootstrap`` verbatim from the M3 analyzer;
  - one confirmatory test per model: a two-sided sign test on the 12 paired
    per-task differences (its floor is p = 2/2^12 = 0.000488);
  - reports BOTH ``verified_final`` (terminal state) and ``verified_checkpoint``
    (anytime, at matched checkpoints) for EVERY arm. Reporting only the former
    would compare SmallCoder's optimal-stopping maximum against the control's
    terminal value and manufacture a gap;
  - runs the preregistered drift check of the fresh treatment arm against the
    frozen M3 arm A, which licenses (or forbids) every frozen-row comparison;
  - applies the integrity rule: a run that edited the fixture's tests is
    ``tampered`` and never counts as solved, symmetrically across arms.

Cost metrics that are not comparable across arms (``tokens_in``, per-run
``duration_s``) are reported but explicitly labelled, never differenced.

Identical inputs produce byte-identical output.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from evals.analyze_m3_generalization import cluster_bootstrap
from evals.analyze_rows import RowsError, fisher_exact_two_sided, load_rows, validate_rows
from evals.run_generic_study import build_plan

BOOTSTRAP_SEED = 20260908
BOOTSTRAP_RESAMPLES = 10_000
TRIALS = 5

# Preregistered: the primary endpoint plus the anytime endpoints.
OUTCOMES = ("verified_final", "verified_checkpoint", "verified_ever")
PRIMARY = "verified_final"
# Preregistered minimum meaningful effect for the falsification criterion.
MIN_MEANINGFUL_EFFECT = 0.05
# Preregistered: below this many finish events, report counts, not rates.
MIN_FINISH_EVENTS_FOR_RATE = 10

EXPLORATORY_COUNTS = (
    "claimed_success",
    "overclaim",
    "silent_success",
    "delivered_success",
    "tampered",
)
COST_METRICS = ("steps", "model_calls", "tokens_out", "chars_sent_total", "peak_context_chars")
NOT_COMPARABLE = ("tokens_in", "duration_s")


class AnalysisError(ValueError):
    """Rows do not match the frozen plan, or an endpoint is missing."""


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text())
    if plan.get("fingerprint") != build_plan(plan["tasks"])["fingerprint"]:
        raise AnalysisError(f"{path} does not match the frozen schedule")
    return plan


def check_rows_against_plan(plan: dict, rows: list[dict]) -> None:
    want = {(e["model"], e["config"], e["task"], e["trial"]) for e in plan["entries"]}
    seen: set[tuple] = set()
    for row in rows:
        key = (row["model"], row["config"], row["task"], row["trial"])
        if key not in want:
            raise AnalysisError(f"row {row.get('run_id')}: key {key} is not in the frozen plan")
        if key in seen:
            raise AnalysisError(f"duplicate row for planned key {key}")
        seen.add(key)
    missing = want - seen
    if missing:
        raise AnalysisError(
            f"{len(missing)} planned run(s) missing, e.g. {sorted(missing)[0]}"
        )


def solved(row: dict, outcome: str) -> int:
    """One success definition, applied identically to every arm.

    The integrity rule is part of the definition: a run that edited the
    fixture's own tests forged the oracle and is never a solve.
    """
    if row.get("tampered"):
        return 0
    value = row.get(outcome)
    if value is None:
        return 0
    return 1 if value else 0


def sign_test(diffs: list[float]) -> dict:
    """Two-sided sign test on paired per-task differences; ties excluded."""
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return {"n_nonzero": 0, "positive": 0, "negative": 0, "p_two_sided": 1.0}
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return {
        "n_nonzero": n,
        "positive": pos,
        "negative": neg,
        "p_two_sided": round(min(1.0, 2 * tail), 6),
        "floor_p": round(2 / (2 ** n), 6),
    }


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def analyze(rows: list[dict], plan: dict, resamples: int) -> dict:
    models, tasks = plan["models"], plan["tasks"]
    configs = [plan["arms"][a] for a in ("S", "G", "GC")]
    result = {
        "design": {
            "runs": len(rows),
            "tasks": tasks,
            "trials": TRIALS,
            "configs": configs,
            "primary_outcome": PRIMARY,
            "min_meaningful_effect": MIN_MEANINGFUL_EFFECT,
            "unit_of_analysis": "task",
            "pooled_across_models": False,
        },
        "per_model": {},
    }

    for model in models:
        block: dict = {"per_task": {}, "arm_totals": {}, "comparisons": {},
                       "exploratory": {}, "cost": {}}
        for config in configs:
            cell = [r for r in rows if r["model"] == model and r["config"] == config]
            block["arm_totals"][config] = {
                outcome: {"hits": sum(solved(r, outcome) for r in cell), "n": len(cell)}
                for outcome in OUTCOMES
            }
            block["exploratory"][config] = {
                name: sum(int(r.get(name) or 0) for r in cell) for name in EXPLORATORY_COUNTS
            }
            block["exploratory"][config]["context_overflow"] = sum(
                1 for r in cell if r.get("stop_reason") == "context_overflow"
            )
            block["cost"][config] = {
                **{m: _mean([r[m] for r in cell if isinstance(r.get(m), int | float)])
                   for m in COST_METRICS},
                **{f"{m}__not_comparable": _mean(
                    [r[m] for r in cell if isinstance(r.get(m), int | float)])
                   for m in NOT_COMPARABLE},
            }

        for task in tasks:
            entry = {}
            for config in configs:
                cell = [r for r in rows
                        if r["model"] == model and r["config"] == config and r["task"] == task]
                entry[config] = {o: sum(solved(r, o) for r in cell) for o in OUTCOMES}
            block["per_task"][task] = entry

        # Preregistered comparisons. S vs G is the confirmatory one.
        treatment, control, decomposition = configs
        for label, (a, b) in {
            "smallcoder_vs_generic": (treatment, control),
            "generic_completion_vs_generic": (decomposition, control),
            "smallcoder_vs_generic_completion": (treatment, decomposition),
        }.items():
            per_outcome = {}
            for outcome in OUTCOMES:
                diffs = [
                    (block["per_task"][t][a][outcome] - block["per_task"][t][b][outcome]) / TRIALS
                    for t in tasks
                ]
                hits_a = block["arm_totals"][a][outcome]
                hits_b = block["arm_totals"][b][outcome]
                per_outcome[outcome] = {
                    "per_task_diffs": [round(d, 3) for d in diffs],
                    "cluster_bootstrap": cluster_bootstrap(diffs, resamples, BOOTSTRAP_SEED),
                    "sign_test": sign_test(diffs),
                    "fisher_descriptive": {
                        "p_two_sided": round(fisher_exact_two_sided(
                            hits_a["hits"], hits_a["n"] - hits_a["hits"],
                            hits_b["hits"], hits_b["n"] - hits_b["hits"]), 6),
                        "note": "treats clustered runs as independent observations",
                    },
                }
            block["comparisons"][label] = per_outcome

        result["per_model"][model] = block
    return result


def falsification_verdict(result: dict) -> dict:
    """Apply the preregistered criteria (a)/(b)/(c) mechanically."""
    verdicts = {}
    for model, block in result["per_model"].items():
        primary = block["comparisons"]["smallcoder_vs_generic"][PRIMARY]
        boot, sign = primary["cluster_bootstrap"], primary["sign_test"]
        anytime = block["comparisons"]["smallcoder_vs_generic"]["verified_checkpoint"]
        thesis_falsified = (
            boot["ci95_high"] < MIN_MEANINGFUL_EFFECT and sign["p_two_sided"] >= 0.05
        )
        any_ci = anytime["cluster_bootstrap"]
        narrows = (
            not thesis_falsified
            and any_ci["ci95_low"] <= 0 <= any_ci["ci95_high"]
        )
        verdicts[model] = {
            "criterion_a_thesis_falsified": thesis_falsified,
            "criterion_b_thesis_narrows": narrows,
            "criterion_c_inconclusive": (
                boot["ci95_low"] <= 0 <= boot["ci95_high"] and not thesis_falsified
            ),
        }
    return verdicts


def drift_check(rows: list[dict], frozen_rows_path: Path) -> dict:
    """Fresh treatment arm vs the frozen M3 arm A. Licenses frozen comparisons."""
    if not frozen_rows_path.is_file():
        return {"available": False}
    frozen = [json.loads(line) for line in
              frozen_rows_path.read_text().splitlines() if line.strip()]
    out = {"available": True, "per_model": {}}
    for model in sorted({r["model"] for r in rows}):
        fresh_cell = [r for r in rows
                      if r["model"] == model and r["config"] == "smallcoder-A"]
        frozen_cell = [r for r in frozen
                       if r["model"] == model and r["config"] == "loop-on+stall-on"]
        out["per_model"][model] = {
            "fresh": {"hits": sum(solved(r, PRIMARY) for r in fresh_cell), "n": len(fresh_cell)},
            "frozen_arm_a": {"hits": sum(1 for r in frozen_cell if r.get("success")),
                             "n": len(frozen_cell)},
        }
    return out


def render_markdown(result: dict, verdicts: dict, drift: dict) -> str:
    d = result["design"]
    treatment, control, decomposition = d["configs"]
    lines = [
        "# Generic agent-loop control study (preregistered)",
        "",
        f"{d['runs']} runs · models analysed separately (no pooled headline) · "
        f"{len(d['tasks'])} tasks × {d['trials']} trials × 3 arms · unit of analysis: task",
        "",
        "Primary endpoint `verified_final` (terminal state). `verified_checkpoint` is the "
        "anytime endpoint at **matched** checkpoints — reported for every arm, because "
        "SmallCoder stops at its first green checkpoint and terminal-only scoring would "
        "compare a maximum against a final value.",
        "",
    ]
    for model, block in result["per_model"].items():
        lines += [f"## {model}", ""]
        lines.append("| arm | verified_final | verified_checkpoint | verified_ever |")
        lines.append("| --- | --- | --- | --- |")
        for config in d["configs"]:
            t = block["arm_totals"][config]
            lines.append(
                f"| `{config}` | {t['verified_final']['hits']}/{t['verified_final']['n']} "
                f"| {t['verified_checkpoint']['hits']}/{t['verified_checkpoint']['n']} "
                f"| {t['verified_ever']['hits']}/{t['verified_ever']['n']} |"
            )
        lines.append("")
        for label, comp in block["comparisons"].items():
            lines.append(f"**{label.replace('_', ' ')}**")
            lines.append("")
            for outcome in OUTCOMES:
                c = comp[outcome]
                b, s = c["cluster_bootstrap"], c["sign_test"]
                lines.append(
                    f"- `{outcome}`: task-cluster bootstrap = {b['point_estimate']:+.3f} "
                    f"(95% CI [{b['ci95_low']:+.3f}, {b['ci95_high']:+.3f}], "
                    f"{b['resamples']} resamples, seed {b['seed']}, unit=task); "
                    f"sign test p = {s['p_two_sided']} "
                    f"({s['positive']}+/{s['negative']}−, floor {s.get('floor_p', '—')}); "
                    f"Fisher p = {c['fisher_descriptive']['p_two_sided']} (descriptive only)"
                )
            lines.append("")
        lines.append("| task | " + " | ".join(f"{c} final" for c in d["configs"])
                     + " | " + " | ".join(f"{c} ckpt" for c in d["configs"]) + " |")
        lines.append("| --- " * (1 + 2 * len(d["configs"])) + "|")
        for task, entry in block["per_task"].items():
            finals = " | ".join(f"{entry[c]['verified_final']}/5" for c in d["configs"])
            ckpts = " | ".join(f"{entry[c]['verified_checkpoint']}/5" for c in d["configs"])
            lines.append(f"| {task} | {finals} | {ckpts} |")
        lines.append("")
        lines.append("Exploratory counts (per arm, 60 runs each):")
        lines.append("")
        lines.append("| arm | " + " | ".join(EXPLORATORY_COUNTS) + " | context_overflow |")
        lines.append("| --- " * (2 + len(EXPLORATORY_COUNTS)) + "|")
        for config in d["configs"]:
            e = block["exploratory"][config]
            lines.append(f"| `{config}` | " + " | ".join(str(e[n]) for n in EXPLORATORY_COUNTS)
                         + f" | {e['context_overflow']} |")
        lines.append("")
        v = verdicts[model]
        lines.append(
            "Preregistered verdict — (a) thesis falsified: "
            f"**{v['criterion_a_thesis_falsified']}**; "
            f"(b) thesis narrows: **{v['criterion_b_thesis_narrows']}**; "
            f"(c) inconclusive: **{v['criterion_c_inconclusive']}**"
        )
        lines.append("")
        finishes = block["exploratory"][control]["claimed_success"]
        if finishes < MIN_FINISH_EVENTS_FOR_RATE:
            lines.append(
                f"> Preregistered interpretation rule: the control produced {finishes} finish "
                f"event(s) (< {MIN_FINISH_EVENTS_FOR_RATE}), so overclaim is reported as a raw "
                "count and no rate difference is computed. A zero overclaim count is evidence "
                "about finish rate, not about calibration."
            )
            lines.append("")
        lines.append("Cost (per run). `tokens_in` and `duration_s` are **not comparable across "
                     "arms** — KV-cache deflation favours the accumulating transcript, and "
                     "SmallCoder's early stop and per-step git/pytest work favour it in the "
                     "other direction — so they are shown, never differenced.")
        lines.append("")
        lines.append("| arm | " + " | ".join(COST_METRICS) + " | tokens_in* | duration_s* |")
        lines.append("| --- " * (3 + len(COST_METRICS)) + "|")
        for config in d["configs"]:
            c = block["cost"][config]
            lines.append(f"| `{config}` | " + " | ".join(str(c[m]) for m in COST_METRICS)
                         + f" | {c['tokens_in__not_comparable']} "
                           f"| {c['duration_s__not_comparable']} |")
        lines.append("")
    if drift.get("available"):
        lines += ["## Drift check — fresh treatment vs frozen M3 arm A", ""]
        for model, entry in drift["per_model"].items():
            f, z = entry["fresh"], entry["frozen_arm_a"]
            lines.append(f"- {model}: fresh {f['hits']}/{f['n']} vs frozen {z['hits']}/{z['n']}")
        lines.append("")
        lines.append("If the fresh rate falls inside the frozen study's per-model interval, "
                     "frozen-row comparisons are licensed and this is also a reproducibility "
                     "result; otherwise every frozen-row comparison is dropped.")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.analyze_generic_study")
    parser.add_argument("--rows", default="results/benchmarks/generic_loop/rows.jsonl")
    parser.add_argument("--plan", default="results/benchmarks/generic_loop/plan.json")
    parser.add_argument("--frozen-rows",
                        default="results/benchmarks/m3_generalization/rows.jsonl")
    parser.add_argument("--resamples", type=int, default=BOOTSTRAP_RESAMPLES)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", dest="fmt")
    args = parser.parse_args(argv)

    try:
        plan = load_plan(Path(args.plan))
        rows = load_rows(args.rows)
        validate_rows(rows)
        check_rows_against_plan(plan, rows)
    except (AnalysisError, RowsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = analyze(rows, plan, args.resamples)
    verdicts = falsification_verdict(result)
    drift = drift_check(rows, Path(args.frozen_rows))
    if args.fmt == "json":
        print(json.dumps({"result": result, "verdicts": verdicts, "drift": drift},
                         indent=2, sort_keys=True))
    else:
        print(render_markdown(result, verdicts, drift), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
