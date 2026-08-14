# Milestone 2B ablation: stall-triggered deterministic verification

**Date:** 2026-08-14
**Design:** 2 models × 2 arms × 5 tasks × 3 trials = **60 runs**, all executed
fresh at commit 48882f2 so the *only* difference between arms is M2B.

- **Arm A — M2A only:** loop detection **on**, stall verification **off**
- **Arm B — M2A+M2B:** loop detection **on**, stall verification **on**

Loop detection is enabled in both arms, as required. No localization, context,
tool-feedback, test-normalization, or prompt changes were made.

## What M2B does

When the working tree has changed but the model has not requested `finish`,
the runtime runs the *same* deterministic verification pipeline it would run at
finish time (changes present → edited-Python syntax → test command). If every
check passes, the runtime completes the run itself.

Bounded and model-invisible by construction: gated by a step interval
(default 5), skipped unless the diff hash changed since the last check,
additionally triggered by a loop detection, and a **failing** check is logged
but never inserted into the prompt. M2B therefore changes no model-facing
behavior — it only changes when the runtime stops.

Completion is recorded in two disjoint categories:
`model_initiated` (the model called `finish` and verification passed,
`stop_reason=verified`) and `runtime_rescued`
(`stop_reason=verified_stall_rescue`).

## Results

| cell | solved | solve rate | model-initiated | runtime-rescued | max_steps | steps | repeats | tokens in | tokens out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1 8B — A (M2A only) | 0/15 | 0% | 0 | 0 | 100% | 30.0 | 11.3 | 30,210 | 1,884 |
| llama3.1 8B — B (M2A+M2B) | 8/15 | 53% | 0 | 8 | 47% | 18.9 | 5.5 | 18,440 | 1,221 |
| qwen2.5-coder 7B — A | 0/15 | 0% | 0 | 0 | 100% | 30.0 | 11.9 | 25,651 | 3,088 |
| qwen2.5-coder 7B — B | 12/15 | 80% | 0 | 12 | 13% | 12.6 | 2.9 | 9,967 | 1,305 |
| **combined A** | **0/30** | **0%** | 0 | 0 | 100% | 30.0 | 11.6 | 27,931 | 2,486 |
| **combined B** | **20/30** | **67%** | 0 | 20 | 30% | 15.8 | 4.2 | 14,204 | 1,263 |

Per task (solved/6 across both models): pagination 0 → 6, storecart 0 → 6,
demo-auth 0 → 4, csvparse 0 → 2, configload 0 → 2.

## Causal effect of M2B alone

| metric | A (M2A only) | B (M2A+M2B) | change |
| --- | --- | --- | --- |
| Solve rate | 0/30 (0%) | 20/30 (67%) | **+67 pts** |
| max_steps rate | 100% | 30% | −70 pts |
| Steps per run | 30.0 | 15.8 | −47% |
| Tool calls per run | 30.0 | 15.7 | −48% |
| Repeated actions per run | 11.6 | 4.2 | −64% |
| Prompt tokens per run | 27,931 | 14,204 | −49% |
| Completion tokens per run | 2,486 | 1,263 | −49% |
| Wall-clock per run | 103 s | 98 s | −5% |

Fisher's exact test on 0/30 vs 20/30 gives p ≈ 1.4 × 10⁻⁸. With n=15 per cell
this remains a small study on five tasks and two models — the *magnitude* of
the improvement should not be treated as a precise estimate — but chance is not
a plausible explanation for the direction or the existence of the effect.

The efficiency gains are a direct consequence, not a separate optimization:
runs terminate the moment the fix verifies (median rescue at **step 5**, range
5–27, 1.6 stall checks per rescue) instead of burning the full 30-step budget.

## The most important caveat: model-initiated completion is still 0

**In all 60 runs, across both arms, `model_initiated` = 0.** Neither <12B model
ever completed a task by its own judgment. Every one of the 20 successes is
attributed to the runtime recognizing a fix the model had already produced but
could not confirm. M2B does not make these models better at deciding they are
done — it makes that decision unnecessary. That is a legitimate systems result
and exactly the SmallCoder thesis, but it must never be reported as the model
having solved the task.

## Why arm B rescued more than arm A's end-state counterfactual predicted

M2A projected ~13/30 rescuable runs (failures whose *final* tree verified
green). Arm B delivered 20/30. Trajectory analysis of arm A explains the gap:
13 runs ended green, and **4 more applied the exact reference fix mid-run and
then destroyed it again** through continued edit churn before step 30 (11 arm-A
runs applied the literal reference fix at some point; 4 of those ended red). So
≥17/30 arm-A runs held a correct fix at some moment and still scored zero.
End-state measurement **understates** the opportunity, because a model left
running past a correct fix frequently breaks it again. Early termination is
part of the mechanism, not just a speed benefit.

## Failure modes that remain (10 failures in arm B)

1. **Wrong or incomplete fix** — the model never produced a passing tree, so
   there was nothing to rescue (configload 4/6 and csvparse 4/6 failures).
   These are comprehension failures that no completion mechanism can fix.
2. **One infrastructure loss** — a qwen csvparse run failed with `model_error`
   after two runner retries (server timeout; that task's runs take up to 690 s).
   It is counted as a failure in the 12/15 above; excluding it gives 12/14.
3. **Slow-model timeout risk** on the longest task remains unaddressed.

## Should the next milestone be something else?

Yes. With M2B in place, the residual failures are no longer *reliability*
failures — they are cases where the model never produced a correct patch at
all. The natural next questions are localization (untested: these fixtures are
still small) and edit-tool feedback (qwen's churn is now cheap but not
eliminated). That decision is out of scope here.

## Files changed for M2B

- `smallcoder/agent/runtime.py` — `_maybe_stall_verify`, rescue branch,
  `completion_mode` / `stall_checks` on `RunResult`, verified-reason handling
- `smallcoder/config.py` — `stall_verification`, `stall_check_interval` + env
- `smallcoder/agent/state.py` — `stall_checks` counter
- `smallcoder/cli.py` — `--stall-verification/--no-stall-verification`, rescue
  labelling in the result panel
- `evals/run_benchmark.py` — `--stall-verification` arm flag, records
  `completion_mode` and `stall_checks`
- `tests/test_stall_verification.py` (new) — 10 tests

## Reproducibility

Commit 48882f2 · Python 3.12.10 · SmallCoder 0.1.0 · models `llama3.1:latest`
(8.0B) and `qwen2.5-coder:7b` (7.6B) · context limit 12000 · max steps 30 ·
stall interval 5 · loop thresholds 3/6/2 · auto-detected pytest verification ·
fresh git baseline per trial. Raw rows: `results/benchmarks/m2b/rows.jsonl`
(60). Command:
`python -m evals.run_benchmark --model MODEL --loop-detector on
--stall-verification on|off --trials 3 --out results/benchmarks/m2b/rows.jsonl`
