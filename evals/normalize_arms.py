"""Make the three arms' rows mean the same thing before anything is compared.

The treatment arm is produced by `evals/run_benchmark.run_one` and the control
arms by `evals/generic_loop.py`, so they record overlapping but not identical
fields. Comparing them raw produces two silent errors, both of which flatter
one arm:

1. **Absent read as zero.** `claimed_success`, `commands_run` and friends exist
   only on control rows. Summing them with ``row.get(k) or 0`` reports the
   treatment arm as a measured zero on every one of them — e.g. "SmallCoder ran
   0 commands", which is false; it simply never recorded the counter.
2. **Asymmetric success definitions.** The integrity rule (a run that edited the
   fixture's own tests forged the oracle and is not a solve) is applied inside
   the control loop but not inside the unmodified runtime, so `success` does not
   mean the same thing on both sides.

This module derives the missing fields for treatment rows from their
trajectories and recorded completion mode, so every arm carries one definition
of every endpoint. Fields that genuinely cannot be recovered are left **absent**
rather than defaulted, so the analyzer reports them as "not measured" instead of
as zero.

Run after `evals/replay_verify.py`, before `evals/analyze_generic_study.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEST_MARKERS = ("tests/", "conftest.py")


def is_tampered(files_changed: list[str] | None) -> int:
    """The verifier runs the repository's own pytest, so the oracle is forgeable."""
    for path in files_changed or []:
        name = Path(path).name
        if path.startswith(TEST_MARKERS[0]) or name == TEST_MARKERS[1] or name.startswith("test_"):
            return 1
    return 0


def count_commands(trajectory: Path) -> int | None:
    """Recover run_command usage for arms that never recorded a counter."""
    if not trajectory.is_file():
        return None
    total = 0
    for line in trajectory.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("event") == "step":
            if (rec.get("action") or {}).get("action_type") == "run_command":
                total += 1
    return total


def normalize(row: dict, runs_dir: Path) -> dict:
    out = dict(row)
    out["tampered"] = int(row.get("tampered") or is_tampered(row.get("files_changed")))

    if "claimed_success" not in out:
        # The runtime gates `finish` behind verification, so a model-initiated
        # completion is a claim that was ALSO verified. That is why the
        # treatment's overclaim count is zero by construction rather than by
        # measurement -- the analyzer must never read it as good calibration.
        mode = row.get("completion_mode")
        out["claimed_success"] = 1 if mode == "model_initiated" else 0
        out["overclaim"] = 0
        out["overclaim_impossible_by_construction"] = 1
        out["silent_success"] = 1 if mode == "runtime_rescued" else 0
        out["delivered_success"] = out["claimed_success"] if row.get("success") else 0

    if "commands_run" not in out:
        recovered = count_commands(runs_dir / row["run_id"] / "trajectory.jsonl")
        if recovered is not None:
            out["commands_run"] = recovered

    # One success definition for every arm, integrity rule included.
    verified = out.get("verified_final")
    if verified is None:
        verified = int(bool(row.get("success")))
        out["verified_final"] = verified
    out["success"] = bool(verified and not out["tampered"])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.normalize_arms")
    parser.add_argument("--rows", required=True)
    parser.add_argument("--runs-dir", default="results/runs")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    runs_dir = Path(args.runs_dir)
    rows = [
        json.loads(line)
        for line in Path(args.rows).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    normalized = [normalize(r, runs_dir) for r in rows]
    with Path(args.out).open("w", encoding="utf-8") as fh:
        for row in normalized:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    flipped = sum(1 for a, b in zip(rows, normalized, strict=True)
                  if bool(a.get("success")) != b["success"])
    tampered = sum(r["tampered"] for r in normalized)
    print(f"[normalize] {len(normalized)} rows; {tampered} tampered; "
          f"{flipped} success value(s) changed by the integrity rule", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
