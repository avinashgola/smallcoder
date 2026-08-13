# Baseline: llama3.1 8B on demo-auth (small-model research baseline)

**Date:** 2026-08-13
**Purpose:** First research baseline for the actual SmallCoder target class
(<12B parameters), using the frozen Milestone 1 runtime with **no** additional
features. 10 trials on one trivial task: an integration-scale sample, not a
statistically significant benchmark.

## Setup

| Item | Value |
| --- | --- |
| SmallCoder version | 0.1.0, commit 2c7108e (Milestone 1 freeze) |
| Python | 3.12.10 |
| Model | `llama3.1:latest` — 8.0B, Q4_K_M (remote Ollama 0.21.0; private host not recorded) |
| Model selection note | Only viable installed <12B text model; not coding-specialized. A 7B coder model (e.g. qwen2.5-coder) is the preferred future target; not downloaded per experiment policy. |
| Task | examples/demo-auth: "Login fails when the email address contains uppercase characters." (repo reset before every trial) |
| Structured output | `OLLAMA_FORMAT=json` |
| Context limit | 12000 tokens (`num_ctx`), ~33.6k char prompt budget |
| Max steps | 30; test command auto-detected `python -m pytest -q --no-header -p no:cacheprovider` |
| Networking | `OLLAMA_FORCE_IPV4=1` |

## Results: 0/10 solved

Every trial ran to the 30-step limit without ever requesting `finish`.

| run_id | steps | model calls | tool calls | malformed actions | repeated actions | failed cmds | files edited | correct fix present at end | tokens in | tokens out | avg latency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| …144139-4c94 | 30 | 30 | 30 | 0 | 12 | 8 | app.py, tests/ | no | 30951 | 1792 | 2.1 s |
| …144244-598c | 30 | 30 | 30 | 0 | 7 | 4 | app.py, tests/ | no | 29491 | 1701 | 1.9 s |
| …144343-64c7 | 30 | 30 | 30 | 0 | 8 | 5 | app.py | no | 30314 | 1807 | 1.8 s |
| …144439-3778 | 30 | 30 | 30 | 0 | 14 | 6 | app.py | no | 31213 | 1801 | 1.8 s |
| …144534-11b2 | 30 | 30 | 30 | 0 | 10 | 4 | app.py | no | 28586 | 1749 | 1.7 s |
| …144628-a594 | 30 | 30 | 30 | 0 | 10 | 7 | app.py, tests/ | no | 30073 | 1769 | 1.8 s |
| …144722-9161 | 30 | 30 | 30 | 0 | 15 | 2 | app.py | no | 27916 | 1714 | 1.8 s |
| …144818-2333 | 30 | 30 | 30 | 0 | 13 | 5 | app.py, tests/ | **yes** | 28904 | 1928 | 1.9 s |
| …144916-eb05 | 30 | 30 | 30 | 0 | 14 | 5 | app.py | **yes** | 29229 | 1829 | 1.8 s |
| …145012-6e77 | 30 | 30 | 30 | 0 | 8 | 5 | app.py, tests/ | no | 29519 | 1835 | 1.8 s |

**Aggregates:** solve rate 0/10 (0%). Steps mean/median 30/30 (hard limit).
Mean tool calls 30, mean tokens in 29,620 / out 1,793, mean call latency
1.84 s. Malformed-action rate **0/300 model calls**. Rejected (disallowed)
tool calls: 0. Repeated actions: mean 11.1 per run (min 7, max 15). Failed
commands: mean 5.1 per run. Verification rejections: 0 — because `finish` was
**never requested in any of the 300 steps**. Files read: `app.py` and
`tests/test_auth.py` in all runs (correct localization). 5/10 runs edited test
files; 2/10 runs ended with the correct one-line fix present but unverified.

**Failure distribution (primary):** REPEATED_ACTION 10/10, with root cause
TEST_INTERPRETATION in all 10 and contributing BAD_EDIT (test-file vandalism)
in 5/10. No STRUCTURED_OUTPUT, INVALID_TOOL_ARGUMENT, LOCALIZATION,
WRONG_FILE, PREMATURE_FINISH, or CONTEXT_OVERFLOW failures occurred.

## The one trap that killed every run

Bare `pytest tests/test_auth.py` cannot `import app` in this fixture (no root
`conftest.py`; only `python -m pytest` puts the cwd on `sys.path`). The 8B
model:

1. runs bare `pytest`, sees `ModuleNotFoundError` — **0/10 runs ever produced
   a working pytest invocation** (the 31B found `python -m pytest` in every
   run, within ~2 attempts);
2. misdiagnoses the harness error as a code/test bug and "fixes" `app.py`
   (sometimes correctly!) or the tests themselves;
3. re-runs the same failing command — one run interleaved
   `python -c 'import app'` (succeeds, cwd on path) with
   `pytest --collect-only` (fails) three times without drawing the conclusion;
4. without a single green signal, never gains confidence to `finish`, and
   loops until max_steps.

Notable trajectory (…144818-2333): the correct fix was applied mid-run, but
with no way to see tests pass, the model reverted to editing
`tests/test_auth.py` repeatedly. The fixture was deliberately left unchanged
during the experiment; this trap is now a measured property of the task.

## Comparison with the 31B integration baseline (same runtime, same task)

| Metric | gemma4:31b (4 runs) | llama3.1 8B (10 runs) |
| --- | --- | --- |
| Solve rate | 4/4 | 0/10 |
| Steps (mean) | 8.75 | 30 (limit) |
| Repeated actions per run | ~1 | 11.1 |
| Malformed actions | 1/37 calls | 0/300 calls |
| Found `python -m pytest` workaround | 4/4 runs | 0/10 runs |
| Edited test files | 0/4 | 5/10 |
| Requested finish | 4/4 (all verified) | 0/10 |
| Tokens in per run (mean) | 9,271 | 29,620 |

The runtime plumbing behaved identically in both experiments; the entire gap
is model behavior — exactly the gap SmallCoder's thesis targets.

## Analysis

1. **Top 3 failure modes:** (a) tool-outcome misinterpretation — a harness
   error (`ModuleNotFoundError`) read as a code defect; (b) repeated-action
   loops — retrying an identical failing command up to 15 times with the
   failure already in context; (c) no completion judgment — `finish` never
   invoked, including twice with the correct fix already applied.
2. **Caused by model capability:** the misdiagnosis itself, the inability to
   synthesize contradictory evidence (`python -c 'import app'` works, pytest
   import fails), and weak strategy switching. These won't be prompted away.
3. **Plausibly eliminated by runtime engineering:** (a) loop detection —
   identical action fingerprints repeated 7–15× per run are trivially
   machine-detectable, and the runtime could interrupt and force a strategy
   change; (b) runtime-owned test execution — the verifier *already knows* the
   correct invocation (`python -m pytest`); normalizing or wrapping test
   commands removes the trap entirely; (c) protected paths for test files;
   (d) runtime-initiated verification when a diff exists and the model stalls
   — which would have solved 2/10 runs outright.
4. **Is repository localization the right Milestone 2?** Not on this evidence.
   Localization never failed: every run read the correct files immediately.
   The demo repo (3 files) cannot express localization failure, so
   localization remains *untested*, not disproven.
5. **What should come first:** reliability engineering — the loop detector,
   bounded recovery, and runtime-owned test execution originally planned as
   Milestone 4 — plus 1–2 multi-file eval fixtures so localization can
   actually be measured before it is built.
6. **Primary metric for Milestone 2:** solve rate on this task (0% baseline),
   with two diagnostic sub-metrics: repeated actions per run (11.1 baseline)
   and share of runs obtaining at least one valid test-execution signal
   (0/10 baseline).

## Reproducibility

Commit 2c7108e · Python 3.12.10 · SmallCoder 0.1.0 · `llama3.1:latest` (8.0B
Q4_K_M) · context limit 12000 · max steps 30 · auto-detected test command ·
run IDs listed above (raw trajectories under `results/runs/`, kept out of git).
