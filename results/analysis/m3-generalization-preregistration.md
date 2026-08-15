# Preregistration: independent M3 generalization study

**Date frozen:** 2026-08-15
**Status:** preregistered before any model has seen these tasks. No Ollama
call, agent run, or benchmark was executed against this suite before the
commit that introduces this document.

## Why this study exists

M3 (deterministic path-resolution feedback, implemented at commit `d50b1aa`)
was designed from the residual-failure analysis of M2B on
`evals/heldout/tasks`, and its ablation was run on those same eight tasks.
That measurement is a valid controlled A/B on its evaluation/design set, but
it is not evidence of generalization. This study supplies the missing test:
a suite authored *after* the M3 implementation freeze, validated only by its
own fixture tests and deterministic reference fixes, and committed before any
model run.

## Frozen evaluation suite

- **Suite:** `evals/m3_generalization/tasks` (12 tasks) with fixtures under
  `evals/m3_generalization/fixtures`. The suite-freeze commit is the Git
  commit that adds this document and the suite together (verify with
  `git log --follow -- results/analysis/m3-generalization-preregistration.md`);
  neither tasks nor fixtures may change afterwards.
- **Validation:** `tests/test_m3_generalization_suite.py` proves, per task:
  spec well-formedness, unique IDs, existing paths, reference `old` matching
  exactly once, fixture tests failing at baseline, the full suite passing
  after only the declared reference fix, and the committed fixture remaining
  byte-identical.
- **Layout balance (fixed before any model output was seen):**
  - root-level relevant file (4): `grading`, `backoff`, `semver`, `leaderboard`
  - uniquely named relevant file in a nested package (4): `ledger`,
    `salesagg`, `amounts`, `booking`
  - duplicate basenames in different directories, where M3 may return
    ambiguous candidate lists (2): `notify` (`format.py` ×2), `invoices`
    (`utils.py` ×2)
  - multi-file causal tasks, symptom and defect in different files (2):
    `receipt` (symptom `pos/receipt.py`, defect `pos/money.py`), `standings`
    (symptom `game/scoreboard.py`, defect `game/stats.py`)
- 8 of 12 fixtures contain realistic irrelevant modules; no fixture contains
  artificial trap directories designed to induce path hallucination.
- Defect categories: boundary logic ×3, parsing ×2, state mutation ×2,
  data transformation ×2, configuration/default ×1, collection logic ×1,
  multi-file behavior ×2 (overlapping the state-mutation and
  data-transformation counts for `standings`/`receipt`).

## Frozen experimental design

- **Runtime:** implementation commit `d50b1aa`. `smallcoder/` must be
  byte-identical to that commit at sweep time; this will be verified and
  reported. No prompt, tool, verifier, threshold, or flag-default change.
- **Models:** `llama3.1:latest` (8.0B Q4_K_M) and `qwen2.5-coder:7b`
  (7.6B Q4_K_M), the same tags/quantizations as the M3 ablation.
- **Arms:**
  - **A:** loop detection ON, stall verification ON, path feedback **OFF**
  - **B:** identical, path feedback **ON**
- **Size:** 12 tasks × 5 trials × 2 models × 2 arms = **240 planned runs.**
- **Settings (all as in the M3 ablation):** max steps 30 · context limit
  12000 (`num_ctx`) · loop thresholds repeat 3 / no-progress window 6 / max
  interventions 2 · stall check interval 5 · sampling temperature 0.2
  (hard-coded in the Ollama client) · `OLLAMA_FORMAT=json` · verification =
  changes present → edited-Python syntax → auto-detected pytest, full suite
  green required for success · fresh temp-dir copy and fresh Git baseline per
  trial.
- **Command template:**
  `python -m evals.run_benchmark --model MODEL --loop-detector on
  --stall-verification on --path-feedback on|off --trials 5
  --tasks-dir evals/m3_generalization/tasks
  --out results/benchmarks/m3_generalization/rows.jsonl`

## Conduct rules (binding)

1. No task, fixture, runtime, prompt, or threshold change after the first
   benchmark run. If a defect in the suite itself is discovered mid-sweep,
   the sweep stops and the whole study restarts from a corrected, re-frozen
   suite; partial results are discarded and the restart is reported.
2. No interim result analysis and no stopping, extending, or re-running based
   on observed performance. The runner's built-in infrastructure handling
   (wait for the server, one retry on `model_error`) is the only permitted
   retry mechanism.
3. Every infrastructure failure, aborted cell, retry, and excluded row is
   reported. Accidental duplicate `model/config/task/trial` rows (e.g. from a
   re-appended aborted cell) are resolved with
   `evals.analyze_rows --dedupe keep-last` and disclosed.
4. Raw rows are committed under `results/benchmarks/m3_generalization/` only
   after a leak scan (no endpoints, hosts, credentials, or `.env` values).
   Trajectories under `results/runs/` stay uncommitted as always.
5. The analysis reports every planned outcome below, whether favorable or not.

## Predeclared outcomes

**Primary mechanism outcome**

- Successful ground-truth-file **read** rate for **llama3.1 8B**, reported
  per task and per arm. A run counts as a GT read if at least one successful
  `read_file` observation of the task's `ground_truth_files` entry appears in
  its trajectory. This is derived from (gitignored) trajectories; only
  sanitized aggregates are published.

**Secondary outcomes** (both models, per arm; from `rows.jsonl` unless noted)

- verified solve rate
- `file_not_found_errors` per run
- suggestion activation (`path_suggestions_emitted`) and follow-through
  (`path_suggestions_followed`)
- steps, prompt/completion tokens, wall-clock per run
- runtime completion mode (`model_initiated` vs `runtime_rescued`)

**Negative control / model-specific expectation**

- Based on the M3 ablation, qwen2.5-coder is expected to show **low**
  suggestion activation; it is **not** preregistered as necessarily zero.
  Whatever activation qwen shows is reported as measured.

## Predeclared statistical analysis

The **task is the primary unit of generalization**; trials are repeated
measurements clustered within tasks, and 240 runs are *not* 240 independent
observations.

- Report raw task-by-arm counts (solves out of 5 trials per task/model/arm)
  and per-task paired arm differences (B − A), per model.
- Interval estimates for arm differences use task-cluster-aware methods:
  a cluster bootstrap resampling the 12 tasks with replacement (10,000
  resamples, seed fixed at 20260815 in the analysis code) on the per-task
  paired differences, per model.
- Run-level Fisher exact tests (as produced by `evals.analyze_rows`) may be
  reported only as **descriptive secondary** analyses, labelled as treating
  clustered runs as observations.
- No combined-model headline number: llama and qwen results are reported
  separately, since the M3 mechanism is expected to be model-specific.
- No claim of general coding-task performance will be made from this study;
  the population is 12 small single-defect Python fixtures.
- Analysis tooling: `evals/analyze_rows.py` for row-level tables; the
  trajectory-derived GT-read extraction and cluster bootstrap will be added
  as a deterministic, tested analysis step in the analysis phase (not
  implemented at preregistration time).

## What would count as what

- **Mechanism replicates:** llama's GT-read rate rises in arm B, concentrated
  in tasks where arm A shows file-not-found errors.
- **Mechanism fails to generalize:** llama arm-A path hallucination is rare
  on this suite (the failure class may be suite-dependent), or GT-read does
  not move despite suggestions firing. Either result is publishable and will
  be reported with equal prominence.
- The ambiguous-candidate tasks (`notify`, `invoices`) probe a behavior the
  first ablation never exercised (multi-candidate suggestion lists); they may
  reveal new failure modes and are reported per task.
