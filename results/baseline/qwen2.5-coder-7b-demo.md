# Baseline: qwen2.5-coder 7B on demo-auth (small-model research baseline #2)

**Date:** 2026-08-13
**Purpose:** Second <12B baseline on the frozen Milestone 1 runtime, using a
coding-specialized model, to test whether llama3.1-8B's failure profile is
representative of the small-model class before choosing Milestone 2. Ten
trials on one trivial task — directional evidence, not statistics.

## Setup

Identical to the llama3.1 baseline (commit 2c7108e, Python 3.12.10, context
limit 12000, max steps 30, `OLLAMA_FORMAT=json`, auto-detected
`python -m pytest` verification, repo reset per trial, `OLLAMA_FORCE_IPV4=1`,
private host not recorded) except the model: **`qwen2.5-coder:7b`** (7.6B,
Q4_K_M, qwen2 family), pulled for this experiment.

## Results: 0/10 solved

Every trial ran to the 30-step limit; `finish` was never requested.

| run_id | steps | malformed actions | repeated actions | failed cmds | files edited | correct fix at end | tokens in | tokens out | avg latency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| …221535-91dc | 30 | 0 | 12 | 2 | app.py, tests/ | no | 26495 | 2937 | 3.1 s |
| …221711-09ae | 30 | 0 | 18 | 0 | app.py, tests/ | no | 25633 | 2867 | 2.9 s |
| …221840-afce | 30 | 0 | 18 | 0 | app.py | **yes** | 27686 | 2712 | 2.9 s |
| …222007-f3a6 | 30 | 0 | 18 | 0 | app.py | no | 27637 | 2956 | 2.7 s |
| …222130-84f3 | 30 | 0 | 20 | 0 | app.py | no | 27475 | 3000 | 2.8 s |
| …222255-a96c | 30 | 0 | 20 | 0 | app.py | **yes** | 26966 | 2988 | 2.8 s |
| …222420-91c5 | 30 | 0 | 12 | 0 | app.py | **yes** | 24086 | 2712 | 2.5 s |
| …222536-2994 | 30 | 0 | 22 | 0 | app.py | no | 26598 | 2821 | 2.6 s |
| …222656-10ec | 30 | 0 | 19 | 0 | app.py | no | 25575 | 2788 | 2.7 s |
| …222816-00a3 | 30 | 0 | 10 | 1 | app.py, tests/ | no | 25560 | 2753 | 2.6 s |

**Aggregates:** solve rate 0/10. Steps 30/30 (limit) in every run. Mean tokens
in 26,371 / out 2,853; mean call latency 2.8 s. Malformed actions **0/300**;
rejected tool calls 0; verification rejections 0 (`finish` never called).
Repeated actions mean 16.9 per run (min 10, max 22 — higher than llama3.1's
11.1). 3/10 runs ended with the correct fix present but unverified; 3/10
edited test files.

**Failure distribution (primary):** REPEATED_ACTION 10/10 — but with a
different root cause than llama3.1: **BAD_EDIT / edit-state amnesia**, not
test misinterpretation.

## The qwen pathology: edit churn without verification

- **8/10 runs never invoked `run_command` at all.** Action mix was almost pure
  read/edit (e.g. 22 edits + 7 reads + 1 search in one run). 0/10 runs ever
  executed pytest — not even a failing invocation. The llama3.1 pytest-import
  trap was therefore never even encountered by 8 of 10 runs.
- **The correct fix usually landed early.** Typical trace (…a96c): step-1-ish
  `edit_file` applies exactly the right change
  (`email.strip()` → `email.strip().lower()`). The model then re-issues the
  same edit, receives `old_text not found` (the file already changed),
  misreads "already applied" as "failed", re-reads, and applies *variants*
  (`email.lower()`, restructured lines) — churning the file it had already
  fixed. One run cycled between just 7 distinct `old_text` values for 22 edit
  attempts.
- **No empirical grounding:** without ever running tests, the model has no
  signal that it is done, and it never develops the confidence to `finish`.

## Three-way comparison (same runtime, same task)

| Metric | gemma4:31b (4) | llama3.1 8B (10) | qwen2.5-coder 7B (10) |
| --- | --- | --- | --- |
| Solve rate | 4/4 | 0/10 | 0/10 |
| Steps (mean) | 8.75 | 30 (limit) | 30 (limit) |
| Repeated actions/run | ~1 | 11.1 | 16.9 |
| Malformed actions | 1/37 calls | 0/300 | 0/300 |
| Ever ran tests | 4/4 | 10/10 (all broken invocations) | 2/10 |
| Green test signal obtained | 4/4 | 0/10 | 0/10 |
| Requested finish | 4/4 | 0/10 | 0/10 |
| Correct fix present at end | 4/4 (verified) | 2/10 (unverified) | 3/10 (unverified) |
| Root cause of failure | — | test-harness misdiagnosis loop | edit-state amnesia, no verification-seeking |

## Analysis update (supersedes single-model conclusions)

1. **The class-level failure modes** across both <12B models: (a) never
   requesting `finish` (0/20 runs) despite the correct fix being present in
   5/20; (b) repeated-action loops (11–17 per run) that a fingerprint check
   detects trivially; (c) failure to obtain — or even seek — a valid test
   signal (0/20 runs saw pytest actually run).
2. **Model capability:** *which* loop each model falls into is model-specific
   (llama: harness misdiagnosis; qwen: edit re-application spiral). The loops
   themselves, and the absent completion judgment, are class-wide.
3. **Runtime-fixable, with expected effect on both models:**
   - **Runtime-initiated verification on stall/loop** — would have converted
     5/20 failed runs (correct fix present) into solves outright, and given
     every other run its first real feedback signal.
   - **Loop detection + strategy interrupt** — both models repeat exact action
     fingerprints far above any reasonable threshold.
   - **Edit-tool feedback**: when `old_text` is absent but `new_text` is
     already present, report "edit already applied" instead of a bare
     not-found error — directly defuses qwen's spiral, deterministically.
   - **Test-command normalization** (bare `pytest` → `python -m pytest`) —
     defuses llama's trap; irrelevant to qwen but harmless.
4. **Localization is still not the bottleneck** — both models located and
   edited the right file in every single run (20/20).
5. **Milestone 2 recommendation (now backed by two models):** reliability —
   loop detection, runtime-initiated verification, bounded recovery, and
   tool-feedback hardening. Repository localization stays deferred until
   multi-file fixtures exist where it can actually fail.
6. **Primary metric:** solve rate (0/20 baseline across <12B models), with
   diagnostics: repeated actions per run (11.1 / 16.9) and share of runs
   obtaining a valid test signal (0/20).

## Reproducibility

Commit 2c7108e · Python 3.12.10 · SmallCoder 0.1.0 · `qwen2.5-coder:7b` (7.6B
Q4_K_M) · context limit 12000 · max steps 30 · auto-detected test command ·
run IDs above (raw trajectories under `results/runs/`, not committed).
