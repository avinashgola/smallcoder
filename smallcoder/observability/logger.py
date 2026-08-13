"""JSONL trajectory logging.

Each run gets a directory under the configured runs dir:

    <runs_dir>/<run_id>/
        meta.json           run configuration
        trajectory.jsonl    one event per line (steps, tool results, errors)
        result.json         final outcome + aggregate metrics
        outputs/            full (untruncated) tool outputs, one file per step
"""

from __future__ import annotations

import json
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path


def new_run_id() -> str:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{secrets.token_hex(2)}"


class TrajectoryLogger:
    def __init__(self, runs_dir: Path, run_id: str | None = None) -> None:
        self.run_id = run_id or new_run_id()
        self.run_dir = runs_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "outputs").mkdir(exist_ok=True)
        self._trajectory = self.run_dir / "trajectory.jsonl"

    def event(self, event_type: str, **fields: object) -> None:
        record = {"ts": time.time(), "event": event_type, **fields}
        with self._trajectory.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def save_output(self, name: str, content: str) -> str:
        """Store a full tool output; returns the path relative to the run dir."""
        rel = f"outputs/{name}"
        (self.run_dir / rel).write_text(content, encoding="utf-8")
        return rel

    def write_meta(self, meta: dict) -> None:
        (self.run_dir / "meta.json").write_text(
            json.dumps(meta, indent=2, default=str), encoding="utf-8"
        )

    def write_result(self, result: dict) -> None:
        (self.run_dir / "result.json").write_text(
            json.dumps(result, indent=2, default=str), encoding="utf-8"
        )


def load_run(runs_dir: Path, run_id: str) -> dict:
    """Load a stored run for inspection. Raises FileNotFoundError if absent."""
    run_dir = runs_dir / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(f"No run found at {run_dir}")
    events = []
    trajectory = run_dir / "trajectory.jsonl"
    if trajectory.exists():
        for line in trajectory.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
    meta_path = run_dir / "meta.json"
    result_path = run_dir / "result.json"
    return {
        "run_id": run_id,
        "meta": json.loads(meta_path.read_text()) if meta_path.exists() else {},
        "result": json.loads(result_path.read_text()) if result_path.exists() else {},
        "events": events,
    }
