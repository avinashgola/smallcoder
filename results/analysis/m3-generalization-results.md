# M3 generalization study: results

**Preregistered.** The design, outcomes, and analysis in this report were fixed
in [`m3-generalization-preregistration.md`](m3-generalization-preregistration.md)
and committed (`70c268d`) before any model saw the suite. Nothing below was
chosen after seeing the data. Every predeclared outcome is reported, favorable
or not, as conduct rule 5 requires.

**Headline:** the M3 mechanism *replicates* — every path suggestion it emitted
was followed, and llama's ground-truth-file read rate reached 100%. Its
**solve-rate benefit does not generalize.** On 12 independently frozen tasks
the path-hallucination failure class that M3 targets is rare (2 of 12 tasks for
llama, 0 of 12 for qwen), and in the runs where the mechanism did fire it
produced no solves at all (0/9). The earlier 13/24 → 19/24 result was
suite-specific.

---

## What was run

240 runs: 12 tasks × 5 trials × 2 models × 2 arms, at runtime commit `d50b1aa`.

- **Arm A:** loop detection on, stall verification on, path feedback **off**
- **Arm B:** identical, path feedback **on**

`smallcoder/` was verified byte-identical to `d50b1aa` at sweep time, and the
runtime settings matched the frozen design exactly (max steps 30, `num_ctx`
12000, `OLLAMA_FORMAT=json`, stall interval 5, loop thresholds 3/6/2).

## Primary outcome — ground-truth-file read rate

Preregistered definition: a run counts as a GT read iff its trajectory contains
a successful `read_file` whose path exactly equals an entry in the task's
`ground_truth_files`. Trajectory-derived; only sanitized aggregates published.

| model | arm A | arm B | task-cluster bootstrap B−A (95% CI) |
| --- | --- | --- | --- |
| llama3.1:latest | 56/60 (93%) | **60/60 (100%)** | +0.067 [+0.000, +0.200] |
| qwen2.5-coder:7b | 44/60 (73%) | 45/60 (75%) | +0.017 [−0.067, +0.117] |

10,000 resamples over the 12 tasks, seed 20260815, unit = task. The llama
interval's lower bound sits exactly on zero; the qwen interval spans zero.

**The reason the effect is small is the important part.** llama's arm-A read
rate was already 93%. The failure mode M3 exists to fix — asking for a
plausible but non-existent path and never recovering — barely occurs on this
suite. In the original M3 study the same arm-A figure was 62%.

## Secondary outcomes

| metric | llama A | llama B | qwen A | qwen B |
| --- | --- | --- | --- | --- |
| verified solve rate | 22/60 (37%) | 23/60 (38%) | 16/60 (27%) | 18/60 (30%) |
| file-not-found errors / run | 2.02 | 1.05 | 0.00 | 0.00 |
| suggestions emitted / run | 0.00 | 1.05 | 0.00 | 0.00 |
| suggestions followed / run | 0.00 | 0.33 | 0.00 | 0.00 |
| steps / run | 21.97 | 23.27 | 24.75 | 24.48 |
| prompt tokens / run | 22,573 | 24,330 | 19,703 | 18,519 |
| completion tokens / run | 1,384 | 1,465 | 2,265 | 2,245 |
| wall-clock / run (s) | 44.6 | 52.3 | 68.7 | 63.3 |

Solve-rate bootstrap: llama +0.017 [−0.067, +0.100]; qwen +0.033 [−0.100,
+0.167]. Both span zero.

**M3 is not free on llama:** +17% wall-clock, +8% prompt tokens, +1.3 steps per
run, for no measurable solve-rate gain on this suite.

### Completion mode

| model / arm | model-initiated | runtime-rescued | no completion |
| --- | --- | --- | --- |
| llama A | 2 | 20 | 38 |
| llama B | 2 | 21 | 37 |
| qwen A | 0 | 16 | 44 |
| qwen B | 0 | 18 | 42 |

Across all 240 runs, **4 completions were model-initiated and 75 of the 79
successes were runtime-attributed (95%)**. This is an incidental but genuine
independent replication of M2B on a suite built for a different purpose: on 12
tasks neither model had seen, small models almost never decided for themselves
that they were finished.

## Where the mechanism actually fired

Per-task file-not-found errors and suggestion activity, llama (all other tasks
were 0 in every column):

| task | A fnf | B fnf | B emitted | B followed | A gt-read | B gt-read | A solved | B solved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backoff | 115 | 32 | 32 | 14 | 1/5 | **5/5** | 0/5 | 0/5 |
| semver | 6 | 31 | 31 | 6 | 5/5 | 5/5 | 0/5 | 0/5 |

`backoff` is M3 working exactly as designed: arm A burned 115 failed path
lookups across 5 runs and reached the right file once; arm B cut that to 32 and
reached it every time. It still solved nothing, because reading the file was
never the only thing standing between this model and a fix.

`semver` runs the other way and is reported as measured: arm B produced *more*
file-not-found errors than arm A (31 vs 6) while both arms read the GT file 5/5.
Path feedback changes the trajectory, so a run that receives a suggestion can go
on to attempt more paths. With one task and n=5 we cannot separate that from
ordinary variance, and we do not claim to.

### Causal chain

Of the 9 llama arm-B runs that emitted at least one suggestion: **9/9 followed a
suggestion, 9/9 then read the ground-truth file, 0/9 solved the task.**

The tool-interaction half of the chain replicates perfectly (the original study
saw 11/11). The solve half does not (the original saw 8/11). On this suite, the
tasks where llama hallucinates paths are also tasks it cannot solve once it gets
there.

### Negative control — qwen

Preregistered expectation: qwen shows *low* suggestion activation, not
necessarily zero. Measured: **exactly zero.** Across all 60 qwen arm-B runs
there were 0 file-not-found errors and 0 suggestions emitted. M3 is a strict
no-op for qwen on this suite, replicating the original finding.

Note that qwen's GT-read rate (73%) is *lower* than llama's (93%) despite zero
path errors. Its misses are not hallucinated paths — it simply never attempts to
read those files (`standings` 0/5 in both arms, `receipt` 1/5 → 0/5). That is a
different failure class, and M3 cannot address it by construction.

### Ambiguous-basename probe

`notify` and `invoices` were frozen in specifically to exercise multi-candidate
suggestion lists, which the first ablation never reached. They generated **zero
file-not-found errors and zero suggestions** in every arm and model. The probe
did not fire, so this study says nothing about ambiguous suggestion behavior. It
remains untested.

## What this counts as

Against the preregistered criteria:

- **"Mechanism replicates"** — partially met. llama's GT-read rate rose in arm B
  and the rise was concentrated in the task where arm A showed file-not-found
  errors, exactly as specified.
- **"Mechanism fails to generalize"** — also met, on the first of its two
  branches: arm-A path hallucination is rare on this suite. The failure class is
  suite-dependent.

Both branches apply, and the honest reading is the conjunction: **M3 reliably
fixes the tool-interaction defect it was built for, but that defect is
uncommon enough on independently authored tasks that fixing it does not improve
task success.**

The preregistration also binds what we may *not* say. No combined-model headline
is reported (`evals.analyze_rows` prints one; it is excluded here by design). No
claim of general coding-task performance is made — the population is 12 small
single-defect Python fixtures. Run-level Fisher tests (llama gt-read p = 0.119,
solve p = 1.0; qwen gt-read p = 1.0, solve p = 0.84) are **descriptive only**:
they treat 240 clustered runs as independent observations, which they are not.

## Verdict: keep M3, and retract the solve-rate claim

Keep it, default on. It is deterministic, adds no model calls, and eliminates a
genuinely degenerate failure mode — 115 wasted lookups on a single task is the
kind of pathology worth engineering away regardless of its effect on the score.

But the M3 write-up's solve-rate framing does not survive contact with an
independent suite and is now re-scoped: M3 **removes a specific tool-interaction
failure**; it does not by itself produce solved tasks. The original 13/24 → 19/24
was already reported as not statistically established (p = 0.125); this study
indicates it was also suite-specific, and the README's existing
suite-provenance caveat was warranted.

This is the value of having preregistered. The mechanism looked better than it
was on the suite it was designed from, and only a frozen, independently authored
suite could show that.

## Disclosures (conduct rule 3)

Every infrastructure failure, aborted cell, and retry:

1. **Aborted cell, 2026-08-15.** Run dir `20260815-170415-115c` — the in-flight
   run when the original sweep was interrupted. No `result.json`, no row
   written; its cell was simply re-run on resume.
2. **Persistent `model_error`, 2026-09-08 11:32, schedule index 57.** Two
   attempts, both failing with `llama runner process has terminated`; the
   scheduler wrote no row and exited resumably per the preregistered policy.
   Root cause was VRAM exhaustion on the remote host — an unrelated resident
   model (`gemma4:31b`, 57.5 GB) left no room to load a study model at the
   frozen `num_ctx=12000`. Confirmed by probe: llama3.1 generated normally at
   `num_ctx=2048` and failed at 12000. Resolved by unloading the resident model;
   **no runtime, task, or threshold was changed**, and no rows entered the
   dataset from these attempts.
3. **Transient `model_error`, schedule index 210.** One failed attempt, retried
   once and succeeded — the only permitted retry mechanism, used once.
4. **No duplicate rows.** All 240 `(model, config, task, trial)` keys are unique,
   so the `--dedupe keep-last` remedy was not needed.
5. The sweep ran in two sessions (57 runs on 2026-08-15, 183 on 2026-09-08).
   One arm pair (llama / `booking` / trial 1) was split across that boundary,
   breaking the scheduler's within-pair temporal-balance property for that
   single pair.

## Reproducibility

```bash
python -m evals.run_m3_generalization --validate      # rows vs the frozen plan
python -m evals.analyze_m3_generalization             # primary + cluster bootstrap
python -m evals.analyze_rows results/benchmarks/m3_generalization/rows.jsonl \
    --expect-cell-size 60                             # secondary outcomes
```

Tracked inputs: `plan.json` (the frozen 240-entry schedule, fingerprinted),
`rows.jsonl` (one row per run), `mechanism.jsonl` (sanitized per-run derived
fields, whitelisted scalars only), and the 12 task specs.

Identical inputs produce byte-identical analyzer output; the bootstrap seed is
fixed at 20260815 in code. Every number in this report except the GT-read counts
and the causal chain is recomputable from `rows.jsonl` alone. GT-read is derived
from trajectories under `results/runs/`, which stay uncommitted (conduct rule 4)
because error strings there can contain the server endpoint —
`mechanism.jsonl` publishes the per-run `gt_read` booleans so the primary
outcome remains checkable without them.
