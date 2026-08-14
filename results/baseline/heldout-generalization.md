# Held-out generalization: M2A-only vs M2A+M2B

**Date:** 2026-08-15
**Status:** held-out result. The runtime was frozen at the M2B commit
(`48882f2`) before these tasks existed; `smallcoder/` was verified
byte-identical to that commit before the sweep. No prompt, threshold, stall
interval, loop parameter, or runtime behavior was tuned on these tasks — they
were authored, validated, committed, and run once.

**Design:** 2 models × 2 arms × 8 new tasks × 3 trials = **96 runs**.
Arm A = loop detection on, stall verification off. Arm B = both on. Loop
detection is enabled in both arms; stall verification is the only variable.

## 1. The held-out suite

Eight tasks, none used in designing M2A or M2B, each validated independently
(tests fail before the reference fix, pass after):

| task | category | defect |
| --- | --- | --- |
| tempconv | simple logic | F→C uses `* 9 / 5` instead of `* 5 / 9` |
| leapyear | simple logic (boundary) | missing the 400-year rule |
| ratelimit | configuration/default | `limits = DEFAULTS` aliases and mutates the global defaults |
| logparse | parsing | `split("\|")` truncates messages containing pipes |
| jsonflat | data transformation | nested leaves lose their key prefix; branches collide |
| inventory | multi-file | symptom in `warehouse/report.py`, defect in `warehouse/stock.py` |
| usergroups | multi-file + irrelevant files | `&=` instead of `\|=`; 4 unrelated modules + docs |
| textstats | logic + irrelevant files | inverted stop-word filter; 8 distractor files (docs/, helpers/, legacy/, reporting/) |

## 2. Results

| cell | solved | rate | model-initiated | runtime-rescued | max_steps | steps | repeats | stall checks | tokens in | tokens out | wall-clock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1 8B — A | 1/24 | 4% | 1 | 0 | 96% | 29.5 | 15.1 | 0 | 27,535 | 1,685 | 55 s |
| llama3.1 8B — B | 11/24 | 46% | 0 | 11 | 54% | 19.2 | 11.9 | 21 | 15,419 | 924 | 33 s |
| qwen2.5-coder 7B — A | 4/24 | 17% | 4 | 0 | 83% | 26.8 | 11.4 | 0 | 23,493 | 2,818 | 83 s |
| qwen2.5-coder 7B — B | 18/24 | 75% | 0 | 18 | 25% | 13.0 | 5.0 | 41 | 10,156 | 1,244 | 38 s |
| **combined A** | **5/48** | **10%** | 5 | 0 | 90% | 28.1 | 13.2 | 0 | 25,514 | 2,251 | 69 s |
| **combined B** | **29/48** | **60%** | 0 | 29 | 40% | 16.1 | 8.4 | 62 | 12,787 | 1,084 | 35 s |

**Effect of M2B on held-out tasks:** solve rate 10% → 60% (+50 pts);
max_steps rate 90% → 40%; steps −43%; prompt tokens −50%; completion tokens
−52%; repeated actions −36%; wall-clock −49%. Fisher's exact on 5/48 vs 29/48
gives p ≈ 4.0 × 10⁻⁷. Structured-output failures: 0 across all 96 runs.

The design-set (M2B) study measured 0/30 → 20/30. The held-out study measures
5/48 → 29/48. The direction and rough magnitude reproduce on tasks the
mechanism was never tuned against.

## 3. Per-task results (solved/3, r = runtime-rescued)

| task | llama A | llama B | qwen A | qwen B |
| --- | --- | --- | --- | --- |
| inventory | 1/3 | 3/3 (r3) | 0/3 | 1/3 (r1) |
| jsonflat | 0/3 | 0/3 | 0/3 | 2/3 (r2) |
| leapyear | 0/3 | 0/3 | 0/3 | 3/3 (r3) |
| logparse | 0/3 | 2/3 (r2) | 0/3 | 2/3 (r2) |
| ratelimit | 0/3 | 0/3 | 3/3 | 3/3 (r3) |
| tempconv | 0/3 | 0/3 | 1/3 | 3/3 (r3) |
| textstats | 0/3 | 3/3 (r3) | 0/3 | 1/3 (r1) |
| usergroups | 0/3 | 3/3 (r3) | 0/3 | 3/3 (r3) |

**No task regressed** in either model. Improvement is broad rather than
concentrated: 6 of 8 tasks improved for at least one model. Repository size
did not block the effect — `textstats` (8 distractor files) went 0/3 → 3/3 for
llama, and `usergroups` (4 unrelated modules) went 0/3 → 3/3 for both models.

## 4. Verification triggers

62 runtime-initiated verification checks fired across arm B (mean 1.3 per run;
0.9 llama, 1.7 qwen). 29 of them ended the run with a passing result; the rest
correctly declined to finish. Arm B ended with **0 failures holding a green
tree**, versus 14 in arm A — M2B captured essentially the whole rescuable
population it was designed for.

## 5. Failures that remain (19 in arm B)

1. **No correct patch was ever produced** — the dominant residual mode. llama
   never solved tempconv, leapyear, jsonflat or ratelimit in any arm; these
   are comprehension failures with nothing to rescue.
2. **Model-capability gap between the two models is large and persists**:
   qwen 75% vs llama 46% in arm B. M2B raises both but does not equalize them.
3. Loop detections stayed high in llama arm B (6.9/run) — churn is cheaper now
   (runs end sooner) but not eliminated.

## 6. An honest nuance about attribution

Arm B records **0 model-initiated completions**, but that is not evidence the
models cannot finish: arm A shows 5 model-initiated solves (1 llama, 4 qwen)
on exactly these tasks. M2B's interval fires at step 5 and frequently
**preempts** a `finish` the model would have reached later — qwen's
`ratelimit` was 3/3 model-initiated in arm A and 3/3 runtime-rescued in arm B,
the same outcome under different attribution. The correct claim is that the
runtime reaches a verified stopping point sooner and far more often, not that
the model became less capable. Every reported success is a deterministic
verification pass (diff present, syntax valid, full test suite green), never a
model assertion.

## 7. Caveats

- n = 3 trials per task-cell; per-task cells are small and individual 3/3 vs
  0/3 entries should be read as directional.
- Tasks are small single-defect fixtures with reliable test suites; a rescue is
  only as trustworthy as the fixture's tests.
- All fixtures except the design-set `demo-auth` include a root `conftest.py`,
  so the bare-`pytest` import trap is not exercised here.
- One infrastructure disruption: the remote inference host became unreachable
  mid-sweep, aborting the llama arm-B cell after 1 run. That cell was re-run in
  full and the single orphan row is excluded from all figures above (raw file
  has 97 rows; 96 analysed, 24 per cell).

## Reproducibility

Runtime commit 48882f2 (frozen) · suite commit 1706fd9 · Python 3.12.10 ·
`llama3.1:latest` (8.0B Q4_K_M), `qwen2.5-coder:7b` (7.6B Q4_K_M) · context
limit 12000 · max steps 30 · stall interval 5 · loop thresholds 3/6/2 ·
auto-detected pytest verification · fresh git baseline per trial. Raw rows:
`results/benchmarks/heldout/rows.jsonl`. Command:
`python -m evals.run_benchmark --model MODEL --loop-detector on
--stall-verification on|off --trials 3 --tasks-dir evals/heldout/tasks
--out results/benchmarks/heldout/rows.jsonl`
