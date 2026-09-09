# Attribution — realbugs

Every fixture under `evals/realbugs/fixtures/` is a **snapshot of a real
open-source repository at the commit immediately before a real bug fix**, with
the fix commit's test changes applied on top. Nothing in these snapshots was
written for this project; full credit belongs to the upstream maintainers and
contributors.

- **Provenance is per task, in the task spec.** Each
  `evals/realbugs/tasks/*.json` records the upstream repository, the fix
  commit SHA, its merge date and its subject line under `"provenance"`. The
  generated [BENCHMARK.md](../../BENCHMARK.md) renders the full table.
- **Licences travel with the code.** Every snapshot retains its upstream
  `LICENSE` / `NOTICE` / `COPYING` files in place — those files, inside each
  fixture, are the authoritative licence for that fixture's code. All mined
  repositories carry permissive licences (MIT / BSD / Apache-2.0); the miner
  never strips a licence file.
- **The conversion is a program, not an editing session.**
  [`evals/mine_realbugs.py`](../mine_realbugs.py) performs every step —
  candidate selection, snapshot, test-patch application, validation, anchored
  fix extraction, issue generation — and rejected candidates are dropped, never
  hand-repaired. Re-running it against the same clones reproduces the suite.
- **Why post-2025 fixes:** every selected fix was merged on or after
  2025-01-01, after the training cutoffs of the models this project studies, so
  the exact patches cannot have been memorized. The library *code* predates the
  cutoff deliberately: a familiar library with an unfamiliar bug is precisely
  the situation a working engineer's model is in.

If you are an upstream maintainer and want a task removed or the attribution
amended, open an issue and it will be done.
