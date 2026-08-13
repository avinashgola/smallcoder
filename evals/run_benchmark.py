"""Minimal ablation benchmark runner (the full evaluation harness is Milestone 5).

Runs each task fixture N times for one model/config cell and appends one JSON
row per run to the output file. Fixtures are copied to a temp dir and given a
fresh git baseline before every trial; agent behavior comes solely from the
SmallCoder runtime under test.

Usage:
  python -m evals.run_benchmark --model MODEL --loop-detector on|off \
      --trials 3 --out results/benchmarks/m2a/rows.jsonl [--task ID ...]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv

from smallcoder.agent.runtime import AgentRuntime
from smallcoder.config import load_settings
from smallcoder.models.base import ModelClientError
from smallcoder.models.ollama import OllamaClient
from smallcoder.observability.logger import TrajectoryLogger

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "evals" / "tasks"


def load_tasks(only: list[str] | None) -> list[dict]:
    tasks = [json.loads(p.read_text()) for p in sorted(TASKS_DIR.glob("*.json"))]
    if only:
        tasks = [t for t in tasks if t["id"] in only]
    return tasks


def prepare_repo(fixture: Path) -> Path:
    workdir = Path(tempfile.mkdtemp(prefix="smallcoder-bench-")) / "repo"
    shutil.copytree(fixture, workdir)
    for argv in (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        ["git", "-c", "user.email=bench@local", "-c", "user.name=bench",
         "commit", "-qm", "baseline"],
    ):
        subprocess.run(argv, cwd=workdir, check=True, capture_output=True)
    return workdir


def wait_for_server(settings, max_wait_s: int = 600) -> bool:
    """Block until the inference server answers, so a transient local network
    outage pauses the benchmark instead of burning trials with model_error."""
    import httpx

    from smallcoder.models.ollama import ForceIPv4Transport

    transport = ForceIPv4Transport() if settings.force_ipv4 else None
    client = httpx.Client(timeout=10, transport=transport)
    deadline = time.monotonic() + max_wait_s
    try:
        while time.monotonic() < deadline:
            try:
                if client.get(settings.base_url + "/api/version").status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            print("[runner] server unreachable, waiting 30s...", flush=True)
            time.sleep(30)
        return False
    finally:
        client.close()


def run_one(task: dict, model_name: str, loop_detector: bool) -> dict:
    settings = load_settings(model=model_name, loop_detector=loop_detector)
    client = OllamaClient(
        base_url=settings.base_url,
        model=settings.model,
        request_timeout=settings.request_timeout,
        structured_format=settings.structured_format,
        num_ctx=settings.context_limit,
        force_ipv4=settings.force_ipv4,
    )
    repo = prepare_repo(ROOT / task["fixture"])
    logger = TrajectoryLogger(settings.runs_dir)
    started = time.monotonic()
    try:
        runtime = AgentRuntime(
            repo_root=repo,
            issue=task["issue"],
            model=client,
            settings=settings,
            logger=logger,
        )
        result = runtime.run()
        row = {
            "run_id": result.run_id,
            "success": result.success,
            "stop_reason": result.stop_reason,
            "steps": result.steps,
            "model_calls": result.model_calls,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "structured_output_failures": result.structured_output_failures,
            "loop_detections": result.loop_detections,
            "loop_interventions": result.loop_interventions,
            "files_changed": result.files_changed,
            "final_verification_passed": (
                result.verification.passed if result.verification else None
            ),
        }
    except ModelClientError as exc:
        row = {"run_id": logger.run_id, "success": False, "stop_reason": "model_error",
               "error": str(exc)[:200]}
    finally:
        client.close()
        shutil.rmtree(repo.parent, ignore_errors=True)
    row["duration_s"] = round(time.monotonic() - started, 1)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--loop-detector", choices=["on", "off"], required=True)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--out", required=True)
    parser.add_argument("--task", action="append", default=None)
    args = parser.parse_args()

    load_dotenv()
    tasks = load_tasks(args.task)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    config = "detector-on" if args.loop_detector == "on" else "detector-off"

    settings_probe = load_settings(model=args.model)
    for task in tasks:
        for trial in range(1, args.trials + 1):
            for attempt in range(2):  # one retry if the network drops mid-run
                if not wait_for_server(settings_probe):
                    print("[runner] server unreachable for 10 minutes, aborting", flush=True)
                    return
                row = run_one(task, args.model, args.loop_detector == "on")
                if row.get("stop_reason") != "model_error":
                    break
                print(f"[runner] {task['id']} trial {trial}: model_error, retrying once",
                      flush=True)
            row.update({"task": task["id"], "trial": trial, "model": args.model,
                        "config": config})
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            print(
                f"[{args.model}/{config}] {task['id']} trial {trial}: "
                f"{'SOLVED' if row.get('success') else row.get('stop_reason')} "
                f"steps={row.get('steps')} loops={row.get('loop_detections')} "
                f"({row.get('duration_s')}s)",
                flush=True,
            )


if __name__ == "__main__":
    main()
