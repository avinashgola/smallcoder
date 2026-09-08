"""Deterministic, resume-safe scheduler for the generic-loop control study.

Executes the frozen 360-run matrix declared in
results/analysis/generic-loop-preregistration.md:
12 tasks x 5 trials x 2 models x 3 arms.

  S  smallcoder-A       the tool-matched treatment (loop + stall on, path off)
  G  generic            the control: accumulating context, finish at face value,
                        no loop detection, no stall verification, no path feedback
  GC generic+completion the decomposition arm: the control plus SmallCoder's
                        completion machinery only

The treatment arm is re-run concurrently rather than reused from the frozen M3
sweep. That costs about two hours and buys back the within-pair temporal
balancing the M3 scheduler exists to provide; reusing rows produced weeks
earlier, on a host with a documented VRAM-contention incident, would discard
exactly the property that makes the comparison defensible.

Schedule construction (SCHEDULE_SEED = 20260908):
  - two model blocks (llama first, then qwen) so each model loads once;
  - within a block the 60 task/trial pairs are shuffled deterministically;
  - within every pair the three arms run in a seeded random order and stay
    ADJACENT, so all three see the same server conditions.

Rows never contain endpoint information: model_error rows are not written, and
any error text is scrubbed of the configured endpoint before serialization.

Usage:
  python -m evals.run_generic_study --write-plan   # materialize plan.json
  python -m evals.run_generic_study --validate     # check rows vs plan
  python -m evals.run_generic_study                # run / resume sweep
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
from pathlib import Path
from urllib.parse import urlsplit

SCHEDULE_SEED = 20260908
MODELS = ["llama3.1:latest", "qwen2.5-coder:7b"]
TRIALS = 5
ARMS = {
    "S": {"config": "smallcoder-A", "kind": "smallcoder"},
    "G": {"config": "generic", "kind": "generic"},
    "GC": {"config": "generic+completion", "kind": "generic_completion"},
}
ARM_ORDER = ["S", "G", "GC"]

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "evals" / "m3_generalization" / "tasks"
OUT_DIR = ROOT / "results" / "benchmarks" / "generic_loop"
PLAN_PATH = OUT_DIR / "plan.json"
ROWS_PATH = OUT_DIR / "rows.jsonl"
META_PATH = OUT_DIR / "meta.json"
# The environment the frozen M3 study ran in; this study must match it.
M3_META_PATH = ROOT / "results" / "benchmarks" / "m3_generalization" / "meta.json"


def load_task_ids() -> list[str]:
    ids = [json.loads(p.read_text())["id"] for p in sorted(TASKS_DIR.glob("*.json"))]
    if len(ids) != 12 or len(set(ids)) != 12:
        raise SystemExit(f"expected 12 unique frozen tasks, found {len(ids)}")
    return sorted(ids)


def build_plan(task_ids: list[str]) -> dict:
    """Materialize the full 360-entry plan. Pure and deterministic."""
    rng = random.Random(SCHEDULE_SEED)
    entries: list[dict] = []
    for model in MODELS:
        pairs = [(task, trial) for task in sorted(task_ids) for trial in range(1, TRIALS + 1)]
        rng.shuffle(pairs)
        for task, trial in pairs:
            order = ARM_ORDER[:]
            rng.shuffle(order)
            for arm in order:
                entries.append({
                    "schedule_index": len(entries),
                    "model": model,
                    "task": task,
                    "trial": trial,
                    "arm": arm,
                    "config": ARMS[arm]["config"],
                })
    plan = {
        "study": "generic-loop-control",
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
    try:
        recomputed = plan_fingerprint(plan)
    except (KeyError, TypeError) as exc:
        raise SystemExit(f"{PLAN_PATH} is missing required plan fields ({exc})") from exc
    if recomputed != plan.get("fingerprint"):
        raise SystemExit(
            f"{PLAN_PATH} is internally inconsistent: its entries no longer hash to its "
            "recorded fingerprint, so the frozen plan has been edited or corrupted"
        )
    if plan_fingerprint(build_plan(plan["tasks"])) != plan["fingerprint"]:
        raise SystemExit("plan.json does not match the frozen schedule (seed/tasks changed?)")
    return plan


def completed_keys(plan: dict, rows: list[dict]) -> set[tuple]:
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
    rows = []
    for lineno, line in enumerate(ROWS_PATH.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"{ROWS_PATH}: line {lineno} is not valid JSON ({exc.msg}). A truncated "
                "trailing line means the sweep was killed mid-write; delete that one line "
                "and resume -- the run it belongs to is simply re-run."
            ) from exc
    return rows


def _endpoint_secrets(settings) -> list[str]:
    parts = urlsplit(settings.base_url)
    secrets = [settings.base_url, parts.netloc, parts.hostname, parts.username, parts.password]
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
            return {scrub(k): scrub(v) for k, v in value.items()}
        return value

    return {k: scrub(v) for k, v in row.items()}


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
        fh.flush()


def check_environment(settings) -> dict:
    """Hard-abort if the inference environment drifted from the M3 study's.

    `llama3.1:latest` is a moving tag. A silent re-pull between the frozen study
    and this one would make every cross-study comparison meaningless, so the
    digests are checked rather than assumed, and the result is published either
    way.
    """
    import httpx

    from smallcoder.models.ollama import ForceIPv4Transport

    expected = json.loads(M3_META_PATH.read_text()) if M3_META_PATH.is_file() else {}
    observed: dict = {"python": platform.python_version(), "models": {}}
    transport = ForceIPv4Transport() if settings.force_ipv4 else None
    with httpx.Client(timeout=30, transport=transport) as client:
        observed["ollama_version"] = client.get(
            settings.base_url + "/api/version").json().get("version")
        for entry in client.get(settings.base_url + "/api/tags").json().get("models", []):
            if entry.get("name") in MODELS and entry.get("digest"):
                observed["models"][entry["name"]] = entry["digest"]

    drift = []
    if expected.get("ollama_version") and observed["ollama_version"] != expected["ollama_version"]:
        drift.append(f"ollama {expected['ollama_version']} -> {observed['ollama_version']}")
    for name, digest in (expected.get("models") or {}).items():
        seen = observed["models"].get(name)
        if seen and seen != digest:
            drift.append(f"{name} digest {digest[:12]} -> {seen[:12]}")
        if not seen:
            drift.append(f"{name} is no longer served")
    observed["m3_environment_match"] = not drift
    observed["drift"] = drift
    if drift:
        raise SystemExit(
            "inference environment drifted from the M3 study: " + "; ".join(drift) +
            ". Cross-study comparisons would be invalid; stopping."
        )
    return observed


def write_environment_meta(observed: dict, settings) -> None:
    """Additive: a later resume must never erase what an earlier block recorded."""
    meta = {"python": platform.python_version(), "models": {}}
    if META_PATH.is_file():
        try:
            previous = json.loads(META_PATH.read_text())
        except json.JSONDecodeError:
            previous = {}
        if isinstance(previous, dict):
            meta = {**previous, **meta}
            meta["models"] = dict(previous.get("models") or {})
    for name, digest in observed.get("models", {}).items():
        recorded = meta["models"].get(name)
        if recorded and recorded != digest:
            raise SystemExit(
                f"model {name} changed digest mid-study ({recorded[:12]} -> {digest[:12]}). "
                "The preregistration freezes model tags, so this is a stop-the-sweep condition."
            )
        meta["models"][name] = digest
    if observed.get("ollama_version"):
        meta["ollama_version"] = observed["ollama_version"]
    meta["m3_environment_match"] = observed.get("m3_environment_match")
    runs_dir = Path(settings.runs_dir)
    if not runs_dir.is_absolute():
        meta["runs_dir"] = runs_dir.as_posix()
    from evals.generic_loop import generic_system_prompt, prompt_digest
    from smallcoder.agent import prompts
    meta["prompt_sha256"] = {
        "smallcoder": prompt_digest(prompts.system_prompt(settings.allowed_commands)),
        "generic": prompt_digest(generic_system_prompt(settings.allowed_commands)),
    }
    META_PATH.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")


def run_sweep() -> int:
    from dotenv import load_dotenv

    load_dotenv()

    from evals.generic_loop import run_one_generic
    from evals.run_benchmark import load_tasks, run_one, wait_for_server
    from smallcoder.config import load_settings

    if Path.cwd().resolve() != ROOT:
        raise SystemExit(
            f"run the sweep from the repository root ({ROOT}). rows.jsonl is repo-anchored "
            "but trajectories and snapshots resolve against the working directory, so "
            "resuming from elsewhere would split them and make anytime scoring impossible."
        )

    plan = load_plan()
    tasks = {t["id"]: t for t in load_tasks(None, TASKS_DIR)}
    if set(tasks) != set(plan["tasks"]):
        raise SystemExit("frozen task set does not match the plan")
    done = completed_keys(plan, load_rows())
    todo = [e for e in plan["entries"]
            if (e["model"], e["config"], e["task"], e["trial"]) not in done]
    total = len(plan["entries"])
    print(f"[scheduler] {len(done)}/{total} runs already recorded; {len(todo)} to go", flush=True)
    if not todo:
        print("[scheduler] plan complete", flush=True)
        return 0

    settings_probe = load_settings(model=plan["models"][0])
    secrets = _endpoint_secrets(settings_probe)
    if not wait_for_server(settings_probe):
        print("[scheduler] server unreachable; exiting resumably", flush=True)
        return 2
    observed = check_environment(settings_probe)
    write_environment_meta(observed, settings_probe)
    print("[scheduler] environment matches the M3 study; digests verified", flush=True)

    for entry in todo:
        kind = ARMS[entry["arm"]]["kind"]
        for attempt in range(2):  # preregistered policy: one retry on model_error
            if not wait_for_server(settings_probe):
                print("[scheduler] server unreachable for 10 minutes; exiting resumably",
                      flush=True)
                return 2
            if kind == "smallcoder":
                row = run_one(tasks[entry["task"]], entry["model"], loop_detector=True,
                              stall_verification=True, path_feedback=False)
            else:
                row = run_one_generic(tasks[entry["task"]], entry["model"],
                                      with_completion=(kind == "generic_completion"))
            if row.get("stop_reason") != "model_error":
                break
            print(f"[scheduler] idx={entry['schedule_index']} model_error "
                  f"(attempt {attempt + 1}); not recorded", flush=True)
        else:
            print("[scheduler] persistent model_error; exiting resumably (no row written)",
                  flush=True)
            return 3
        row.update({
            "task": entry["task"],
            "trial": entry["trial"],
            "model": entry["model"],
            "config": entry["config"],
            "arm": entry["arm"],
            "schedule_index": entry["schedule_index"],
        })
        append_row(sanitize_row(row, secrets))
        done.add((entry["model"], entry["config"], entry["task"], entry["trial"]))
        print(f"[scheduler] [{len(done)}/{total}] idx={entry['schedule_index']} "
              f"{entry['model']} {entry['task']} t{entry['trial']} arm{entry['arm']} "
              f"recorded ({row.get('duration_s')}s, steps={row.get('steps')}, "
              f"success={row.get('success')})", flush=True)
    print("[scheduler] plan complete", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.run_generic_study")
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
