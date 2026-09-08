"""Offline *anytime* scoring — the fix for the study's worst confound.

SmallCoder stops the instant its stall check sees a green tree, so its recorded
solve rate is an optimal-stopping maximum. The generic control has no such
check and almost always runs to `max_steps`, so scoring it only at its terminal
state would compare a maximum against a final value: a control run that fixes
the bug at step 12 and breaks it again by step 30 would score zero for purely
measurement reasons. That alone would manufacture most of a gap.

This module replays verification over the per-step working-tree snapshots that
`evals/generic_loop.py` writes, and produces two extra endpoints:

``verified_checkpoint``
    The headline anytime number. It replays SmallCoder's *own* checkpoint
    gating byte for byte (tree changed since baseline, at least
    ``stall_check_interval`` steps since the last check, and the working-tree
    diff hash actually moved), so the control gets neither more nor fewer
    sampling opportunities than the treatment. Over-correcting here — verifying
    every single step — would flip the unfairness the other way.

``verified_ever``
    Exploratory only: verification at every snapshot. Reported as an upper
    bound, never as the headline.

The same replay runs against the SmallCoder arms, where it should reproduce
their recorded `success` almost exactly. That agreement is the evidence that
both arms are being scored by one estimator rather than two.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from smallcoder.config import load_settings
from smallcoder.gitutils import changed_since, snapshot, working_tree_diff
from smallcoder.recovery.loop_detector import diff_state_hash
from smallcoder.verification.verifier import verify

ROOT = Path(__file__).resolve().parent.parent


def edits_up_to(trajectory: Path, step: int) -> list[str]:
    """Files edited on or before ``step``, deduped in insertion order.

    An empty list makes verify() skip the python_syntax check entirely, so this
    has to mirror AgentState.note_edit rather than approximate it.
    """
    edited: list[str] = []
    if not trajectory.is_file():
        return edited
    for line in trajectory.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("event") != "step" or rec.get("step", 0) > step:
            continue
        action = rec.get("action") or {}
        if action.get("action_type") == "edit_file" and rec.get("ok"):
            path = (action.get("arguments") or {}).get("path")
            if path and path not in edited:
                edited.append(path)
    return edited


def _verify_snapshot(snap: Path, settings, edited: list[str]) -> bool:
    """Copy a snapshot to a scratch dir and run the real verifier on it."""
    with tempfile.TemporaryDirectory(prefix="smallcoder-replay-") as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(snap, work, symlinks=True)
        base = snapshot(work)
        # The snapshot carries the fixture's own baseline commit, so the
        # baseline recomputed here is the same one the run was scored against.
        return verify(work, settings, base, edited, None).passed


def replay_run(run_dir: Path, settings) -> dict:
    """Return anytime endpoints for one run directory."""
    snap_dir = run_dir / "snapshots"
    trajectory = run_dir / "trajectory.jsonl"
    if not snap_dir.is_dir():
        return {"verified_checkpoint": None, "verified_ever": None, "checkpoints": 0}

    steps = sorted(
        (int(p.name.split("_")[1]), p)
        for p in snap_dir.iterdir()
        if p.is_dir() and p.name.startswith("step_")
    )
    verified_checkpoint = 0
    verified_ever = 0
    checkpoints = 0
    last_check_step = 0
    last_diff_hash: str | None = None

    for step, snap in steps:
        if step == 0:
            continue
        edited = edits_up_to(trajectory, step)
        # --- exploratory: every step
        if not verified_ever and _verify_snapshot(snap, settings, edited):
            verified_ever = 1
        # --- headline: SmallCoder's own checkpoint gating, replayed
        with tempfile.TemporaryDirectory(prefix="smallcoder-gate-") as tmp:
            work = Path(tmp) / "repo"
            shutil.copytree(snap, work, symlinks=True)
            base = snapshot(work)
            if not changed_since(work, base):
                continue
            if (step - last_check_step) < settings.stall_check_interval:
                continue
            diff_hash = diff_state_hash(working_tree_diff(work))
            if diff_hash == last_diff_hash:
                continue
            last_check_step, last_diff_hash = step, diff_hash
            checkpoints += 1
            passed = verify(work, settings, base, edited, None).passed
        if passed and not verified_checkpoint:
            verified_checkpoint = 1

    return {
        "verified_checkpoint": verified_checkpoint,
        "verified_ever": verified_ever,
        "checkpoints": checkpoints,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.replay_verify")
    parser.add_argument("--rows", required=True, help="rows.jsonl to annotate")
    parser.add_argument("--runs-dir", default="results/runs")
    parser.add_argument("--out", required=True, help="annotated rows.jsonl to write")
    args = parser.parse_args(argv)

    settings = load_settings(model="replay")
    runs_dir = Path(args.runs_dir)
    rows = [
        json.loads(line)
        for line in Path(args.rows).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    annotated = []
    for n, row in enumerate(rows, start=1):
        extra = replay_run(runs_dir / row["run_id"], settings)
        annotated.append({**row, **extra})
        print(f"[replay] {n}/{len(rows)} {row['run_id']} "
              f"checkpoint={extra['verified_checkpoint']} ever={extra['verified_ever']} "
              f"({extra['checkpoints']} checkpoints)", flush=True)

    with Path(args.out).open("w", encoding="utf-8") as fh:
        for row in annotated:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"[replay] wrote {len(annotated)} rows to {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
