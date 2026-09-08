"""Tests for the generic-loop study scheduler and its preregistered analyzer.

Synthetic data only — no model, no network.
"""

from __future__ import annotations

import json

import pytest

from evals.analyze_generic_study import (
    AnalysisError,
    analyze,
    check_rows_against_plan,
    falsification_verdict,
    render_markdown,
    sign_test,
    solved,
)
from evals.analyze_generic_study import main as analyze_main
from evals.run_generic_study import (
    ARMS,
    MODELS,
    TRIALS,
    build_plan,
    completed_keys,
    load_task_ids,
    plan_fingerprint,
    sanitize_row,
)

TASK_IDS = load_task_ids()


# ------------------------------------------------------------- scheduler


def test_plan_is_deterministic_and_complete():
    a, b = build_plan(TASK_IDS), build_plan(TASK_IDS)
    assert a == b
    assert len(a["entries"]) == len(TASK_IDS) * TRIALS * len(MODELS) * len(ARMS) == 360
    assert a["fingerprint"] == plan_fingerprint(a)


def test_the_three_arms_run_adjacently_in_varying_order():
    """All three arms must see the same server conditions for each task/trial."""
    entries = build_plan(TASK_IDS)["entries"]
    orders = set()
    for i in range(0, len(entries), 3):
        group = entries[i:i + 3]
        assert len({(g["model"], g["task"], g["trial"]) for g in group}) == 1
        assert {g["arm"] for g in group} == set(ARMS)
        orders.add(tuple(g["arm"] for g in group))
    assert len(orders) > 1, "arm order must be randomized, not fixed"


def test_completed_keys_rejects_unplanned_and_duplicate_rows():
    plan = build_plan(TASK_IDS)
    entry = plan["entries"][0]
    row = {k: entry[k] for k in ("model", "config", "task", "trial", "schedule_index")}
    assert completed_keys(plan, [row]) == {
        (row["model"], row["config"], row["task"], row["trial"])
    }
    with pytest.raises(SystemExit, match="duplicate"):
        completed_keys(plan, [row, dict(row)])
    with pytest.raises(SystemExit, match="not in the frozen plan"):
        completed_keys(plan, [{**row, "task": "nope"}])


def test_sanitize_row_scrubs_endpoints_in_keys_and_values():
    row = {"error": {"10.0.0.5": "connection to http://10.0.0.5:11434 refused"}}
    out = sanitize_row(row, ["http://10.0.0.5:11434", "10.0.0.5"])
    assert "10.0.0.5" not in json.dumps(out)


# -------------------------------------------------------------- analysis


def test_sign_test_matches_known_values():
    assert sign_test([0.0] * 12)["p_two_sided"] == 1.0
    all_positive = sign_test([0.2] * 12)
    assert all_positive["p_two_sided"] == pytest.approx(2 / 2 ** 12, abs=1e-6)
    assert sign_test([0.2, -0.2])["p_two_sided"] == 1.0


def test_tampered_runs_never_count_as_solved_in_any_arm():
    """The oracle is forgeable; the integrity rule is part of the definition."""
    honest = {"verified_final": 1, "tampered": 0}
    forged = {"verified_final": 1, "tampered": 1}
    assert solved(honest, "verified_final") == 1
    assert solved(forged, "verified_final") == 0


def test_unmeasured_endpoint_is_none_not_zero():
    """An endpoint one arm cannot measure must never be reported as a zero.

    verified_ever needs per-step snapshots and the treatment arm takes none, so
    scoring it 0/60 would invent a catastrophic result for that arm and make
    every comparison against it meaningless.
    """
    assert solved({"verified_final": 1}, "verified_checkpoint") is None
    assert solved({"verified_checkpoint": 0}, "verified_checkpoint") == 0


def test_unmeasurable_outcomes_are_not_differenced(tmp_path):
    plan, rows, _, _ = build_synthetic_study(tmp_path)
    for row in rows:
        if row["arm"] == "S":
            row.pop("verified_ever")
    result = analyze(rows, plan, 100)
    for model in MODELS:
        comp = result["per_model"][model]["comparisons"]["smallcoder_vs_generic"]
        assert comp["verified_ever"].get("unavailable") is True
        assert "cluster_bootstrap" not in comp["verified_ever"]
        assert comp["verified_final"].get("unavailable") is None


def build_synthetic_study(tmp_path, treatment_hits=4, control_hits=1):
    """A complete 360-row study with a controllable treatment effect."""
    plan = build_plan(TASK_IDS)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    rows = []
    for entry in plan["entries"]:
        arm = entry["arm"]
        hits = treatment_hits if arm == "S" else control_hits
        # trial 1..hits succeed, deterministically
        win = entry["trial"] <= hits
        rows.append({
            "run_id": f"r{entry['schedule_index']}",
            "success": bool(win),
            "stop_reason": "max_steps" if arm != "S" else "verified_stall_rescue",
            "task": entry["task"], "trial": entry["trial"], "model": entry["model"],
            "config": entry["config"], "arm": arm,
            "schedule_index": entry["schedule_index"],
            "verified_final": int(win), "verified_checkpoint": int(win),
            "verified_ever": int(win), "tampered": 0,
            "claimed_success": 0, "overclaim": 0, "silent_success": int(win),
            "delivered_success": 0,
            "steps": 30, "model_calls": 31, "tokens_in": 1000, "tokens_out": 200,
            "duration_s": 60.0, "chars_sent_total": 5000, "peak_context_chars": 900,
        })
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return plan, rows, plan_path, rows_path


def test_full_analysis_pipeline_on_a_complete_study(tmp_path, capsys):
    plan, _, plan_path, rows_path = build_synthetic_study(tmp_path)
    code = analyze_main([
        "--rows", str(rows_path), "--plan", str(plan_path),
        "--frozen-rows", str(tmp_path / "absent.jsonl"), "--resamples", "200",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "Generic agent-loop control study (preregistered)" in out
    for model in MODELS:
        assert model in out
    assert "smallcoder-A" in out and "generic" in out and "generic+completion" in out
    # a real treatment effect must show as a positive bootstrap point estimate
    assert "smallcoder vs generic" in out
    assert "not comparable across arms" in out


def test_analysis_is_deterministic(tmp_path):
    plan, _, plan_path, rows_path = build_synthetic_study(tmp_path)
    runs = []
    for _ in range(2):
        rows = [json.loads(x) for x in rows_path.read_text().splitlines() if x.strip()]
        runs.append(json.dumps(analyze(rows, plan, 200), sort_keys=True))
    assert runs[0] == runs[1]


def test_analysis_refuses_partial_data(tmp_path):
    plan, rows, plan_path, rows_path = build_synthetic_study(tmp_path)
    rows_path.write_text("\n".join(json.dumps(r) for r in rows[:100]) + "\n")
    code = analyze_main([
        "--rows", str(rows_path), "--plan", str(plan_path), "--resamples", "50",
    ])
    assert code == 1, "a partial sweep must not be analysable (no interim analysis)"


def test_check_rows_against_plan_requires_exactly_one_row_per_key(tmp_path):
    plan, rows, _, _ = build_synthetic_study(tmp_path)
    check_rows_against_plan(plan, rows)
    with pytest.raises(AnalysisError, match="missing"):
        check_rows_against_plan(plan, rows[:-1])


def test_falsification_verdict_fires_when_there_is_no_effect(tmp_path):
    """A genuine null must trip criterion (a), not be quietly reported as a win."""
    plan, rows, _, _ = build_synthetic_study(tmp_path, treatment_hits=1, control_hits=1)
    verdicts = falsification_verdict(analyze(rows, plan, 400))
    for model in MODELS:
        assert verdicts[model]["criterion_a_thesis_falsified"] is True


def test_falsification_verdict_does_not_fire_on_a_large_effect(tmp_path):
    plan, rows, _, _ = build_synthetic_study(tmp_path, treatment_hits=5, control_hits=0)
    verdicts = falsification_verdict(analyze(rows, plan, 400))
    for model in MODELS:
        assert verdicts[model]["criterion_a_thesis_falsified"] is False


def test_render_includes_the_finish_interpretation_rule(tmp_path):
    plan, rows, _, _ = build_synthetic_study(tmp_path)
    result = analyze(rows, plan, 200)
    text = render_markdown(result, falsification_verdict(result), {"available": False})
    # the synthetic control never calls finish, so the preregistered rule must fire
    assert "evidence about finish rate, not about calibration" in text


# ------------------------------------------------- cross-arm normalization
#
# The two runners record overlapping but different fields. These guard the two
# ways that asymmetry silently flatters one arm.


def test_absent_counters_are_not_reported_as_measured_zeros(tmp_path):
    from evals.normalize_arms import normalize
    row = {"run_id": "x", "success": True, "completion_mode": "runtime_rescued",
           "files_changed": ["a.py"]}
    out = normalize(row, tmp_path)          # no trajectory on disk
    assert "commands_run" not in out, "an unrecoverable counter must stay absent, not become 0"


def test_treatment_claims_are_derived_from_completion_mode():
    from pathlib import Path as P

    from evals.normalize_arms import normalize
    rescued = normalize({"run_id": "a", "success": True,
                         "completion_mode": "runtime_rescued", "files_changed": ["a.py"]},
                        P("/nonexistent"))
    claimed = normalize({"run_id": "b", "success": True,
                         "completion_mode": "model_initiated", "files_changed": ["a.py"]},
                        P("/nonexistent"))
    assert rescued["silent_success"] == 1 and rescued["claimed_success"] == 0
    assert claimed["claimed_success"] == 1 and claimed["delivered_success"] == 1
    # the runtime gates finish behind verification, so this is structural, not calibration
    assert claimed["overclaim"] == 0
    assert claimed["overclaim_impossible_by_construction"] == 1


def test_integrity_rule_is_applied_symmetrically():
    from pathlib import Path as P

    from evals.normalize_arms import is_tampered, normalize
    assert is_tampered(["tests/test_x.py"]) == 1
    assert is_tampered(["conftest.py"]) == 1
    assert is_tampered(["pkg/test_helpers.py"]) == 1
    assert is_tampered(["backoff.py"]) == 0
    forged = normalize({"run_id": "c", "success": True, "completion_mode": "model_initiated",
                        "files_changed": ["tests/test_x.py"]}, P("/nonexistent"))
    assert forged["tampered"] == 1 and forged["success"] is False
