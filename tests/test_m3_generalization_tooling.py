"""Tests for the M3 generalization scheduler and preregistered analyzer.

Everything here runs on synthetic data — no model, no network.
"""

import json
from pathlib import Path

import pytest

from evals.analyze_m3_generalization import (
    AnalysisError,
    analyze,
    check_rows_against_plan,
    cluster_bootstrap,
    derive_mechanism_rows,
    gt_read_from_trajectory,
    load_task_specs,
)
from evals.analyze_m3_generalization import (
    main as analyze_main,
)
from evals.run_m3_generalization import (
    ARMS,
    MODELS,
    build_plan,
    completed_keys,
    load_task_ids,
    plan_fingerprint,
    sanitize_row,
)

TASK_IDS = load_task_ids()


# ---------------------------------------------------------------- scheduler


def test_plan_is_deterministic_and_complete():
    plan_a = build_plan(TASK_IDS)
    plan_b = build_plan(TASK_IDS)
    assert plan_a == plan_b
    assert plan_a["fingerprint"] == plan_fingerprint(plan_b)
    entries = plan_a["entries"]
    assert len(entries) == 240
    keys = {(e["model"], e["config"], e["task"], e["trial"]) for e in entries}
    assert len(keys) == 240
    assert [e["schedule_index"] for e in entries] == list(range(240))


def test_plan_model_blocks_and_cell_sizes():
    entries = build_plan(TASK_IDS)["entries"]
    assert all(e["model"] == MODELS[0] for e in entries[:120])
    assert all(e["model"] == MODELS[1] for e in entries[120:])
    for model in MODELS:
        for arm in ARMS:
            cell = [e for e in entries if e["model"] == model and e["arm"] == arm]
            assert len(cell) == 60
            for task in TASK_IDS:
                assert sum(1 for e in cell if e["task"] == task) == 5


def test_plan_arm_pairs_are_adjacent_and_order_randomized():
    entries = build_plan(TASK_IDS)["entries"]
    first_arms = []
    for i in range(0, 240, 2):
        first, second = entries[i], entries[i + 1]
        assert (first["model"], first["task"], first["trial"]) == (
            second["model"], second["task"], second["trial"]
        )
        assert {first["arm"], second["arm"]} == {"A", "B"}
        first_arms.append(first["arm"])
    # the seeded coin flip must actually vary the order
    assert "A" in first_arms and "B" in first_arms


def make_row(entry, **overrides):
    row = {
        "run_id": f"run-{entry['schedule_index']:03d}",
        "success": entry["arm"] == "B",
        "stop_reason": "verified_stall_rescue" if entry["arm"] == "B" else "max_steps",
        "steps": 10,
        "tokens_in": 5000,
        "tokens_out": 400,
        "duration_s": 20.0,
        "completion_mode": "runtime_rescued" if entry["arm"] == "B" else "none",
        "file_not_found_errors": 0,
        "path_suggestions_emitted": 0,
        "path_suggestions_followed": 0,
        "task": entry["task"],
        "trial": entry["trial"],
        "model": entry["model"],
        "config": entry["config"],
        "arm": entry["arm"],
        "schedule_index": entry["schedule_index"],
    }
    row.update(overrides)
    return row


def test_completed_keys_accepts_valid_subset():
    plan = build_plan(TASK_IDS)
    rows = [make_row(e) for e in plan["entries"][:10]]
    assert len(completed_keys(plan, rows)) == 10


def test_completed_keys_rejects_duplicates_unknowns_and_index_mismatch():
    plan = build_plan(TASK_IDS)
    entry = plan["entries"][0]
    with pytest.raises(SystemExit, match="duplicate"):
        completed_keys(plan, [make_row(entry), make_row(entry)])
    with pytest.raises(SystemExit, match="not in the frozen plan"):
        completed_keys(plan, [make_row(entry, trial=99)])
    with pytest.raises(SystemExit, match="schedule_index mismatch"):
        completed_keys(plan, [make_row(entry, schedule_index=7)])


def test_sanitize_row_scrubs_endpoint_strings():
    row = {"error": "connect to http://10.1.2.3:11434 failed", "nested": ["10.1.2.3"]}
    clean = sanitize_row(row, ["http://10.1.2.3:11434", "10.1.2.3:11434", "10.1.2.3"])
    assert "10.1.2.3" not in json.dumps(clean)
    assert "<endpoint>" in clean["error"]


# ----------------------------------------------------------------- analyzer


def test_check_rows_against_plan_requires_exactly_one_row_per_key():
    plan = build_plan(TASK_IDS)
    rows = [make_row(e) for e in plan["entries"]]
    check_rows_against_plan(plan, rows)  # complete: passes

    with pytest.raises(AnalysisError, match="missing"):
        check_rows_against_plan(plan, rows[:-1])
    with pytest.raises(AnalysisError, match="duplicate"):
        check_rows_against_plan(plan, rows + [rows[0]])
    with pytest.raises(AnalysisError, match="unplanned"):
        bad = make_row(plan["entries"][0], model="other-model")
        check_rows_against_plan(plan, rows + [bad])


def write_trajectory(runs_dir, run_id, records):
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "trajectory.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records)
    )


def step(action_type, path, ok):
    return {
        "event": "step",
        "action": {"action_type": action_type, "arguments": {"path": path}},
        "ok": ok,
    }


def test_gt_read_extraction_rules(tmp_path):
    gt = ["bank/ledger.py"]
    write_trajectory(tmp_path, "hit", [step("read_file", "bank/ledger.py", True)])
    write_trajectory(tmp_path, "wrong-path", [step("read_file", "src/ledger.py", True)])
    write_trajectory(tmp_path, "failed-read", [step("read_file", "bank/ledger.py", False)])
    write_trajectory(tmp_path, "edit-only", [step("edit_file", "bank/ledger.py", True)])

    assert gt_read_from_trajectory(tmp_path / "hit" / "trajectory.jsonl", gt)
    assert not gt_read_from_trajectory(tmp_path / "wrong-path" / "trajectory.jsonl", gt)
    assert not gt_read_from_trajectory(tmp_path / "failed-read" / "trajectory.jsonl", gt)
    assert not gt_read_from_trajectory(tmp_path / "edit-only" / "trajectory.jsonl", gt)


def test_missing_and_malformed_trajectories_fail_clearly(tmp_path):
    with pytest.raises(AnalysisError, match="missing trajectory"):
        gt_read_from_trajectory(tmp_path / "nope" / "trajectory.jsonl", ["a.py"])
    run_dir = tmp_path / "bad"
    run_dir.mkdir()
    (run_dir / "trajectory.jsonl").write_text("{not json\n")
    with pytest.raises(AnalysisError, match="malformed trajectory"):
        gt_read_from_trajectory(run_dir / "trajectory.jsonl", ["a.py"])


def test_cluster_bootstrap_is_deterministic_and_task_level():
    diffs = [0.2] * 12
    first = cluster_bootstrap(diffs, 500, 20260815)
    second = cluster_bootstrap(diffs, 500, 20260815)
    assert first == second
    # constant per-task diffs must collapse the interval to the point estimate
    assert first["point_estimate"] == first["ci95_low"] == first["ci95_high"] == 0.2
    assert first["unit"] == "task"

    # resampling 12 task diffs of {0, 1.2} can only produce means that are
    # multiples of 0.1; run-level resampling (60 runs) would produce 1/50ths
    spread = cluster_bootstrap([0.0] * 11 + [1.2], 500, 20260815)
    lo_steps = round(spread["ci95_low"] / 0.1, 6)
    hi_steps = round(spread["ci95_high"] / 0.1, 6)
    assert lo_steps == int(lo_steps) and hi_steps == int(hi_steps)


def build_synthetic_study(tmp_path):
    """Full 240-run synthetic study: gt_read iff arm B; solved iff arm B on
    the first six tasks (alphabetical)."""
    plan = build_plan(TASK_IDS)
    specs = load_task_specs
    solved_tasks = set(TASK_IDS[:6])
    runs_dir = tmp_path / "runs"
    rows = []
    for entry in plan["entries"]:
        row = make_row(entry, success=entry["arm"] == "B" and entry["task"] in solved_tasks)
        rows.append(row)
        gt = json.loads(
            (Path("evals/m3_generalization/tasks") / f"{entry['task']}.json").read_text()
        )["ground_truth_files"][0]
        path = gt if entry["arm"] == "B" else "src/" + gt.rsplit("/", maxsplit=1)[-1]
        write_trajectory(runs_dir, row["run_id"], [step("read_file", path, True)])
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    return plan, rows, runs_dir, rows_path, plan_path, specs


def test_full_analysis_pipeline_and_sanitization(tmp_path, capsys):
    plan, rows, runs_dir, rows_path, plan_path, _ = build_synthetic_study(tmp_path)
    derived_path = tmp_path / "mechanism.jsonl"
    args = [
        "--rows", str(rows_path),
        "--plan", str(plan_path),
        "--runs-dir", str(runs_dir),
        "--derived-out", str(derived_path),
        "--resamples", "300",
        "--format", "json",
    ]
    assert analyze_main(args) == 0
    first_out = capsys.readouterr().out
    first_derived = derived_path.read_bytes()

    result = json.loads(first_out)
    for model in MODELS:
        block = result["per_model"][model]
        gt = block["outcomes"]["gt_read"]
        assert gt["arm_totals"]["A"] == {"hits": 0, "n": 60}
        assert gt["arm_totals"]["B"] == {"hits": 60, "n": 60}
        assert gt["cluster_bootstrap"]["point_estimate"] == 1.0
        assert gt["cluster_bootstrap"]["ci95_low"] == 1.0
        solved = block["outcomes"]["success"]
        assert solved["arm_totals"]["B"] == {"hits": 30, "n": 60}
        assert solved["cluster_bootstrap"]["point_estimate"] == 0.5
        assert block["fisher_descriptive"]["gt_read"]["note"].startswith("descriptive")
    assert "combined" not in first_out

    # sanitization: whitelisted keys only, no endpoint-ish or user-path values
    allowed = {
        "run_id", "schedule_index", "model", "config", "arm", "task", "trial",
        "success", "gt_read", "file_not_found_errors", "path_suggestions_emitted",
        "path_suggestions_followed", "steps", "tokens_in", "tokens_out",
        "duration_s", "completion_mode",
    }
    for line in first_derived.decode().splitlines():
        record = json.loads(line)
        assert set(record) <= allowed
        blob = json.dumps(record)
        assert "http" not in blob and "/Users/" not in blob and "observation" not in blob

    # determinism: identical inputs -> identical bytes
    assert analyze_main(args) == 0
    assert capsys.readouterr().out == first_out
    assert derived_path.read_bytes() == first_derived


def test_analysis_fails_on_missing_trajectory(tmp_path):
    plan = build_plan(TASK_IDS)
    rows = [make_row(e) for e in plan["entries"][:2]]
    specs = load_task_specs(Path("evals/m3_generalization/tasks"))
    with pytest.raises(AnalysisError, match="missing trajectory"):
        derive_mechanism_rows(rows, specs, tmp_path / "empty-runs")


def test_analyze_reports_ambiguous_tasks_separately(tmp_path):
    plan, rows, runs_dir, *_ = build_synthetic_study(tmp_path)
    specs = load_task_specs(Path("evals/m3_generalization/tasks"))
    derived = derive_mechanism_rows(rows, specs, runs_dir)
    result = analyze(derived, plan, resamples=50)
    assert result["design"]["ambiguous_candidate_tasks"] == ["invoices", "notify"]
    for task in ("invoices", "notify"):
        assert task in result["per_model"][MODELS[0]]["per_task"]


# ------------------------------------------------ resume/provenance hardening
#
# The sweep is long, restartable, and runs against an intermittently reachable
# host. These cover the failure modes that would silently corrupt the study
# rather than stop it: a half-written row, an edited frozen plan, a failed
# metadata probe erasing unrecoverable provenance, and a resume from the wrong
# working directory splitting rows from their trajectories.

import httpx

from evals.run_m3_generalization import (
    ROOT,
    _endpoint_secrets,
    load_plan,
    load_rows,
    run_sweep,
    write_environment_meta,
)


class _Settings:
    force_ipv4 = False
    base_url = "http://192.0.2.10:11434"
    runs_dir = Path("results/runs")


def test_load_rows_reports_a_truncated_line_recoverably(tmp_path, monkeypatch):
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text('{"a": 1}\n{"b": 2}\n{"c": ')  # killed mid-write
    monkeypatch.setattr("evals.run_m3_generalization.ROWS_PATH", rows_path)
    with pytest.raises(SystemExit) as exc:
        load_rows()
    assert "line 3" in str(exc.value)
    assert "resume" in str(exc.value)


def test_load_plan_rejects_an_internally_inconsistent_plan(tmp_path, monkeypatch):
    plan = build_plan(TASK_IDS)
    plan["entries"][0]["trial"] = 99  # tamper, leave the recorded fingerprint alone
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    monkeypatch.setattr("evals.run_m3_generalization.PLAN_PATH", plan_path)
    with pytest.raises(SystemExit, match="internally inconsistent"):
        load_plan()


def test_load_plan_accepts_the_frozen_plan(tmp_path, monkeypatch):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(build_plan(TASK_IDS)))
    monkeypatch.setattr("evals.run_m3_generalization.PLAN_PATH", plan_path)
    assert load_plan()["fingerprint"] == plan_fingerprint(build_plan(TASK_IDS))


def _fake_httpx(monkeypatch, digest, version="0.21.0"):
    class _Response:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            if url.endswith("/api/version"):
                return _Response({"version": version})
            return _Response({"models": [{"name": MODELS[0], "digest": digest}]})

    monkeypatch.setattr(httpx, "Client", _Client)


def test_environment_meta_survives_a_failed_probe(tmp_path, monkeypatch):
    """A resume during an outage must not erase digests it cannot re-probe."""
    meta_path = tmp_path / "meta.json"
    recorded = {"a" * 8: "1" * 64, "b" * 8: "2" * 64}
    meta_path.write_text(json.dumps({"models": recorded, "ollama_version": "0.21.0"}))
    monkeypatch.setattr("evals.run_m3_generalization.META_PATH", meta_path)

    def _boom(*args, **kwargs):
        raise RuntimeError("host unreachable")

    monkeypatch.setattr(httpx, "Client", _boom)
    write_environment_meta(_Settings())

    after = json.loads(meta_path.read_text())
    assert after["models"] == recorded
    assert after["ollama_version"] == "0.21.0"
    assert after["runs_dir"] == "results/runs"
    assert _Settings.base_url not in meta_path.read_text()


def test_environment_meta_aborts_when_a_model_digest_changes(tmp_path, monkeypatch):
    """Swapped model weights invalidate the frozen design — stop, don't resume."""
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps({"models": {MODELS[0]: "f" * 64}}))
    monkeypatch.setattr("evals.run_m3_generalization.META_PATH", meta_path)
    _fake_httpx(monkeypatch, digest="e" * 64)
    with pytest.raises(SystemExit, match="changed digest mid-study"):
        write_environment_meta(_Settings())


def test_environment_meta_records_an_unchanged_digest(tmp_path, monkeypatch):
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps({"models": {MODELS[0]: "f" * 64}}))
    monkeypatch.setattr("evals.run_m3_generalization.META_PATH", meta_path)
    _fake_httpx(monkeypatch, digest="f" * 64, version="0.21.0")
    write_environment_meta(_Settings())
    after = json.loads(meta_path.read_text())
    assert after["models"][MODELS[0]] == "f" * 64
    assert after["ollama_version"] == "0.21.0"


def test_sweep_refuses_to_resume_from_another_working_directory(tmp_path, monkeypatch):
    """rows.jsonl is repo-anchored; trajectories are cwd-relative. Never split them."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="repository root"):
        run_sweep()
    assert Path.cwd().resolve() != ROOT


def test_endpoint_secrets_cover_url_credentials():
    class _WithCreds:
        base_url = "http://user:pw@10.0.0.5:11434"

    secrets = _endpoint_secrets(_WithCreds())
    assert "user" in secrets and "pw" in secrets and "10.0.0.5" in secrets


def test_sanitize_row_scrubs_dict_keys_as_well_as_values():
    row = {"error": {"10.0.0.5": "refused"}}
    assert sanitize_row(row, ["10.0.0.5"]) == {"error": {"<endpoint>": "refused"}}
