"""Deterministic, resume-safe scheduler for the preregistered M3 generalization sweep.

Executes the frozen 240-run matrix from
results/analysis/m3-generalization-preregistration.md:
12 tasks x 5 trials x 2 models x 2 arms, at runtime commit d50b1aa behavior
(this module changes nothing about the runtime; it only orders and records
runs, reusing evals.run_benchmark's run_one / wait_for_server verbatim).

Schedule construction (SCHEDULE_SEED = 20260815, documented here and in the
plan file):
  - two model blocks (llama first, then qwen) so each model loads once;
  - within a block, the 60 task/trial pairs are shuffled deterministically;
  - within every pair, one seeded coin flip decides whether arm A or arm B
    runs first, and the two arm runs stay adjacent so temporal/server
    conditions are balanced within the pair.

The full plan is materialized (plan.json, sanitized: no endpoint or
environment values) before any model call. Every planned run has a stable
schedule_index and a unique (model, config, task, trial) key.

Resume: completed rows are validated against the frozen plan; only planned,
not-yet-done keys execute. Duplicate rows, unknown keys, or a plan/seed
mismatch abort. Ordinary unsuccessful agent runs are never re-run. A run that
ends in model_error (infrastructure) is retried once after re-waiting for the
server, per the preregistered policy; if it still fails, nothing is written
and the scheduler exits resumably — model_error rows are never persisted,
because every committed row must have a trajectory for GT-read extraction.

Rows never contain endpoint information: model_error rows are not written,
and any error text that did flow through is scrubbed of the configured
endpoint before serialization.

Usage:
  python -m evals.run_m3_generalization --write-plan   # materialize plan.json
  python -m evals.run_m3_generalization --validate     # check rows vs plan
  python -m evals.run_m3_generalization                # run / resume sweep
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import time
from pathlib import Path
from urllib.parse import urlsplit

SCHEDULE_SEED = 20260815
MODELS = ["llama3.1:latest", "qwen2.5-coder:7b"]
TRIALS = 5
ARMS = {
    "A": {"path_feedback": False, "config": "loop-on+stall-on"},
    "B": {"path_feedback": True, "config": "loop-on+stall-on+path-on"},
}

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "evals" / "m3_generalization" / "tasks"
OUT_DIR = ROOT / "results" / "benchmarks" / "m3_generalization"
PLAN_PATH = OUT_DIR / "plan.json"
ROWS_PATH = OUT_DIR / "rows.jsonl"
META_PATH = OUT_DIR / "meta.json"


def load_task_ids() -> list[str]:
    ids = [json.loads(p.read_text())["id"] for p in sorted(TASKS_DIR.glob("*.json"))]
    if len(ids) != 12 or len(set(ids)) != 12:
        raise SystemExit(f"expected 12 unique frozen tasks, found {len(ids)}")
    return sorted(ids)


def build_plan(task_ids: list[str]) -> dict:
    """Materialize the full 240-entry plan. Pure and deterministic."""
    rng = random.Random(SCHEDULE_SEED)
    entries = []
    for model in MODELS:
        pairs = [(task, trial) for task in sorted(task_ids) for trial in range(1, TRIALS + 1)]
        rng.shuffle(pairs)
        for task, trial in pairs:
            first = "A" if rng.random() < 0.5 else "B"
            for arm in (first, "B" if first == "A" else "A"):
                entries.append(
                    {
                        "schedule_index": len(entries),
                        "model": model,
                        "task": task,
                        "trial": trial,
                        "arm": arm,
                        "config": ARMS[arm]["config"],
                    }
                )
    plan = {
        "study": "m3-generalization",
        "schedule_seed": SCHEDULE_SEED,
        "models": MODELS,
        "trials": TRIALS,
        "arms": {arm: spec["config"] for arm, spec in ARMS.items()},
        "tasks": sorted(task_ids),
        "entries": entries,
    }
    plan["fingerprint"] = plan_fingerprint(plan)
    return plan


def plan_fingerprint(plan: dict) -> str:
    payload = json.dumps(
        {k: plan[k] for k in ("schedule_seed", "models", "trials", "arms", "tasks", "entries")},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def row_key(row: dict) -> tuple:
    return (row["model"], row["config"], row["task"], row["trial"])


def load_plan() -> dict:
    if not PLAN_PATH.is_file():
        raise SystemExit(f"no plan at {PLAN_PATH}; run --write-plan first")
    plan = json.loads(PLAN_PATH.read_text())
    rebuilt = build_plan(plan["tasks"])
    if plan.get("fingerprint") != rebuilt["fingerprint"]:
        raise SystemExit("plan.json does not match the frozen schedule (seed/tasks changed?)")
    return plan


def completed_keys(plan: dict, rows: list[dict]) -> set[tuple]:
    """Validate persisted rows against the plan; return the completed key set."""
    by_key = {(e["model"], e["config"], e["task"], e["trial"]): e for e in plan["entries"]}
    seen: set[tuple] = set()
    for n, row in enumerate(rows, start=1):
        key = row_key(row)
        if key not in by_key:
            raise SystemExit(f"row {n}: key {key} is not in the frozen plan")
        if key in seen:
            raise SystemExit(f"row {n}: duplicate planned key {key}")
        if row.get("schedule_index") != by_key[key]["schedule_index"]:
            raise SystemExit(f"row {n}: schedule_index mismatch for {key}")
        seen.add(key)
    return seen


def load_rows() -> list[dict]:
    if not ROWS_PATH.is_file():
        return []
    return [json.loads(line) for line in ROWS_PATH.read_text().splitlines() if line.strip()]


def _endpoint_secrets(settings) -> list[str]:
    parts = urlsplit(settings.base_url)
    secrets = [settings.base_url]
    if parts.netloc:
        secrets.append(parts.netloc)
    if parts.hostname:
        secrets.append(parts.hostname)
    return [s for s in secrets if s]


def sanitize_row(row: dict, secrets: list[str]) -> dict:
    def scrub(value):
        if isinstance(value, str):
            for secret in secrets:
                value = value.replace(secret, "<endpoint>")
            return value
        if isinstance(value, list):
            return [scrub(v) for v in value]
        if isinstance(value, dict):
            return {k: scrub(v) for k, v in value.items()}
        return value

    return {k: scrub(v) for k, v in row.items()}


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
        fh.flush()


def write_environment_meta(settings) -> None:
    """Record python/ollama/model-digest metadata. Never the server location."""
    import httpx

    from smallcoder.models.ollama import ForceIPv4Transport

    meta = {"python": platform.python_version(), "models": {}}
    transport = ForceIPv4Transport() if settings.force_ipv4 else None
    try:
        with httpx.Client(timeout=10, transport=transport) as client:
            version = client.get(settings.base_url + "/api/version").json().get("version")
            meta["ollama_version"] = version
            tags = client.get(settings.base_url + "/api/tags").json().get("models", [])
            for entry in tags:
                if entry.get("name") in MODELS:
                    meta["models"][entry["name"]] = entry.get("digest")
    except Exception:
        pass  # metadata is optional; never block or leak on failure
    META_PATH.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")


def run_sweep() -> int:
    from dotenv import load_dotenv

    load_dotenv()

    from evals.run_benchmark import load_tasks, run_one, wait_for_server
    from smallcoder.config import load_settings

    plan = load_plan()
    tasks = {t["id"]: t for t in load_tasks(None, TASKS_DIR)}
    if set(tasks) != set(plan["tasks"]):
        raise SystemExit("frozen task set does not match the plan")
    done = completed_keys(plan, load_rows())
    todo = [
        e for e in plan["entries"]
        if (e["model"], e["config"], e["task"], e["trial"]) not in done
    ]
    total = len(plan["entries"])
    print(f"[scheduler] {len(done)}/{total} runs already recorded; {len(todo)} to go", flush=True)
    if not todo:
        print("[scheduler] plan complete", flush=True)
        return 0

    settings_probe = load_settings(model=plan["models"][0])
    secrets = _endpoint_secrets(settings_probe)
    write_environment_meta(settings_probe)

    for entry in todo:
        for attempt in range(2):  # preregistered policy: one retry on model_error
            if not wait_for_server(settings_probe):
                print("[scheduler] server unreachable for 10 minutes; exiting resumably",
                      flush=True)
                return 2
            started = time.monotonic()
            row = run_one(
                tasks[entry["task"]],
                entry["model"],
                loop_detector=True,
                stall_verification=True,
                path_feedback=ARMS[entry["arm"]]["path_feedback"],
            )
            if row.get("stop_reason") != "model_error":
                break
            print(
                f"[scheduler] idx={entry['schedule_index']} model_error "
                f"(attempt {attempt + 1}); not recorded",
                flush=True,
            )
        else:
            print("[scheduler] persistent model_error; exiting resumably (no row written)",
                  flush=True)
            return 3
        row.update(
            {
                "task": entry["task"],
                "trial": entry["trial"],
                "model": entry["model"],
                "config": entry["config"],
                "arm": entry["arm"],
                "schedule_index": entry["schedule_index"],
            }
        )
        append_row(sanitize_row(row, secrets))
        done.add((entry["model"], entry["config"], entry["task"], entry["trial"]))
        print(
            f"[scheduler] [{len(done)}/{total}] idx={entry['schedule_index']} "
            f"{entry['model']} {entry['task']} t{entry['trial']} arm{entry['arm']} "
            f"recorded ({round(time.monotonic() - started)}s, steps={row.get('steps')})",
            flush=True,
        )
    print("[scheduler] plan complete", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.run_m3_generalization")
    parser.add_argument("--write-plan", action="store_true",
                        help="Materialize the frozen plan.json and exit.")
    parser.add_argument("--validate", action="store_true",
                        help="Validate existing rows against the plan and exit.")
    args = parser.parse_args(argv)

    if args.write_plan:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        plan = build_plan(load_task_ids())
        if PLAN_PATH.is_file():
            existing = json.loads(PLAN_PATH.read_text())
            if existing.get("fingerprint") != plan["fingerprint"]:
                raise SystemExit("refusing to overwrite a different frozen plan")
        PLAN_PATH.write_text(json.dumps(plan, indent=1) + "\n")
        print(f"[scheduler] plan written: {len(plan['entries'])} runs, "
              f"fingerprint {plan['fingerprint'][:16]}", flush=True)
        return 0
    if args.validate:
        plan = load_plan()
        done = completed_keys(plan, load_rows())
        print(f"[scheduler] {len(done)}/{len(plan['entries'])} planned runs recorded; "
              "rows are consistent with the frozen plan", flush=True)
        return 0
    return run_sweep()


if __name__ == "__main__":
    raise SystemExit(main())
