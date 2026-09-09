"""Prove the published numbers reproduce from tracked data — byte for byte.

Every analyzer in this repository is deterministic, and every number in the
reports derives from tracked rows. This module turns that from a claim into a
CI gate: it re-runs every analysis against the committed data and diffs the
output against golden copies under ``results/analysis/golden/``. Any drift —
in the data, the analyzers, or their dependencies — fails the build.

Usage:
  python -m evals.check_reproducibility             # verify (CI mode)
  python -m evals.check_reproducibility --bless     # regenerate the goldens
"""

from __future__ import annotations

import argparse
import contextlib
import difflib
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "results" / "analysis" / "golden"


def _capture(fn, argv: list[str]) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(argv)
    if code != 0:
        raise RuntimeError(f"analyzer exited {code} for argv={argv}")
    return buf.getvalue()


def outputs() -> dict[str, str]:
    from evals.analyze_generic_study import main as generic_main
    from evals.analyze_m3_generalization import main as m3_main
    from evals.analyze_rows import main as rows_main

    result: dict[str, str] = {}
    for name, argv in {
        "rows-m2a.md": ["results/benchmarks/m2a/rows.jsonl"],
        "rows-m2b.md": ["results/benchmarks/m2b/rows.jsonl"],
        "rows-heldout.md": ["results/benchmarks/heldout/rows.jsonl", "--dedupe", "keep-last"],
        "rows-m3.md": ["results/benchmarks/m3/rows.jsonl"],
        "rows-m3-generalization.md": ["results/benchmarks/m3_generalization/rows.jsonl"],
        "rows-generic-loop.md": ["results/benchmarks/generic_loop/rows_final.jsonl"],
    }.items():
        result[name] = _capture(rows_main, argv)

    # The study analyzer writes a derived mechanism file; point it at a temp
    # path so verification never touches tracked artifacts.
    with tempfile.TemporaryDirectory() as tmp:
        result["study-m3-generalization.md"] = _capture(
            m3_main, ["--derived-out", f"{tmp}/mechanism.jsonl"])
    result["study-generic-loop.md"] = _capture(
        generic_main, ["--rows", "results/benchmarks/generic_loop/rows_final.jsonl"])
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.check_reproducibility")
    parser.add_argument("--bless", action="store_true",
                        help="write the current outputs as the new goldens")
    args = parser.parse_args(argv)

    fresh = outputs()
    if args.bless:
        GOLDEN.mkdir(parents=True, exist_ok=True)
        for name, text in fresh.items():
            (GOLDEN / name).write_text(text, encoding="utf-8")
        print(f"blessed {len(fresh)} golden outputs into {GOLDEN}")
        return 0

    failures = 0
    for name, text in fresh.items():
        golden_path = GOLDEN / name
        if not golden_path.is_file():
            print(f"MISSING golden: {name} (run with --bless)", file=sys.stderr)
            failures += 1
            continue
        golden = golden_path.read_text(encoding="utf-8")
        if golden != text:
            failures += 1
            diff = list(difflib.unified_diff(
                golden.splitlines(), text.splitlines(),
                f"golden/{name}", f"recomputed/{name}", lineterm=""))[:20]
            print(f"DRIFT in {name}:", file=sys.stderr)
            print("\n".join(diff), file=sys.stderr)
    if failures:
        print(f"\n{failures} output(s) no longer reproduce", file=sys.stderr)
        return 1
    print(f"all {len(fresh)} published analyses reproduce byte-identically")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
