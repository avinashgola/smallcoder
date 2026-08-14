# Milestone 2A ablation: loop detection alone

**Date:** 2026-08-13/14
**Design:** 2 models × 2 configurations × 5 tasks × 3 trials = **60 runs**.
Configuration A is the frozen Milestone 1 runtime (`--no-loop-detector`);
configuration B adds *only* the M2A loop detector. No other agent behavior
changed. 60 runs on 5 tasks is directional evidence, **not** statistical
significance; single-solve differences are within noise.

## 1. Benchmark suite

| task | category | fixture | ground-truth file(s) | reference fix |
| --- | --- | --- | --- | --- |
| demo-auth | reliability stress (bare-`pytest` import trap, preserved) | examples/demo-auth | app.py | lowercase email on login lookup |
| pagination | simple logic/boundary | evals/fixtures/pagination | pagination.py | off-by-one slice end |
| configload | configuration/default | evals/fixtures/configload | settings.py | `bool("false")` truthiness |
| storecart | multi-file behavior | evals/fixtures/storecart | store/discounts.py (+cart.py) | `percent/10` → `percent/100` |
| csvparse | parser/data transformation | evals/fixtures/csvparse | csv_utils.py | strip whitespace around fields |

Each fixture ships reproducible failing tests and a machine-applicable
reference fix; all five were validated to fail before and pass after the
reference fix. The four new fixtures include a root `conftest.py`, so bare
`pytest` works — the import trap is now isolated to demo-auth by design.

**Config:** commit d0b9fed/95eabb8, Python 3.12.10, context limit 12000, max
steps 30, `OLLAMA_FORMAT=json`, auto-detected pytest verification, fresh git
baseline per trial, loop thresholds: repeat ≥3, no-progress window 6, max 2
interventions. Private endpoint not recorded.

## 2/3. Results

| cell | solved | solve rate | max_steps rate | steps (mean) | tool calls | repeats/run | detections/run | interventions/run | tokens in | tokens out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1 8B, detector **off** | 1/15 | 7% | 93% | 29.7 | 29.7 | 10.2 | — | — | 31,934 | 2,027 |
| llama3.1 8B, detector **on** | 1/15 | 7% | 93% | 29.0 | 28.9 | 10.8 | 0.6 | 0.6 | 30,095 | 1,849 |
| qwen2.5-coder 7B, detector **off** | 1/15 | 7% | 93% | 29.4 | 29.3 | 13.1 | — | — | 28,002 | 3,046 |
| qwen2.5-coder 7B, detector **on** | 2/15 | 13% | 87% | 28.6 | 28.5 | 10.9 | 1.8 | 1.0 | 23,476 | 2,900 |

Per task (solved/3): only csvparse (llama-on, qwen-on) and pagination
(qwen-off, qwen-on) and storecart (llama-off) were ever solved. **configload
and demo-auth: 0/12 each across all cells.** Structured-output failures: 0
across all 60 runs (1,780+ model calls).

## 4. Absolute and relative change (B vs A)

| metric | llama3.1 8B | qwen2.5-coder 7B | combined |
| --- | --- | --- | --- |
| Solve rate | 7% → 7% (0) | 7% → 13% (+1 run) | 2/30 → 3/30 (+3.3 pts) |
| max_steps rate | 93% → 93% | 93% → 87% | 93% → 90% |
| Repeated actions/run | 10.2 → 10.8 (+6%) | 13.1 → 10.9 (−17%) | 11.7 → 10.9 (−7%) |
| Tokens in/run | 31,934 → 30,095 (−6%) | 28,002 → 23,476 (−16%) | −11% |
| Steps/run | 29.7 → 29.0 | 29.4 → 28.6 | −2% |

**Verdict: loop detection alone does not meaningfully improve solve rate.**
The single extra qwen solve is within noise for n=15. The consistent,
believable effect is a **~11% reduction in prompt tokens** (history compaction
on intervention) and a modest repeat reduction for qwen. The mechanism works —
it just is not the binding constraint.

**Why detections fired rarely.** Across the 30 detector-on runs there were 326
raw `(action_type, arguments)` repeats and 79 patterns repeated 3+ times, but
only 36 detections. The fingerprint additionally requires an identical
working-tree diff hash *and* identical result signature, so a re-issued action
that changes the repository (or yields a different error) is deliberately not
counted as a loop. This is correct by design — it avoids interrupting genuine
progress — but it means the detector is silent during the most common
pathology: **repeated *edits* that keep mutating the file** (208 repeated
identical `edit_file` calls across all 60 runs).

## 5. Failure modes that remain

1. **Never requesting `finish` — the dominant failure.** In **20 of 55 failed
   runs (36%)**, the final verification passed *every* check
   (`changes_present`, `python_syntax`, pytest green): the repository held a
   complete, correct, test-passing fix and the run was still scored a failure
   because the model never called `finish` before max_steps. Per cell: 4/14,
   6/14 (llama off/on), 5/14, 5/13 (qwen off/on).
2. **Edit churn on an already-correct file** (qwen especially): re-applying an
   edit, receiving `old_text not found`, and mutating further.
3. **Semantic-comprehension failures** on configload (0/12) and demo-auth
   (0/12) — the truthiness bug and the import trap were never diagnosed.
4. **Step budget exhausted by exploration** — 90% of runs hit max_steps.

## 6. Should M2B be stall-triggered verification? **Yes — the evidence is unambiguous.**

36% of all failures already contain a verified-passing fix. A runtime rule of
the form *"if the working tree has changed and the model has not finished
within N steps (or a loop was detected), run the verification pipeline; if it
passes, finish the run"* would convert those runs into solves without any new
model capability. Projected effect if it had been active in this study:
solve rate **3/60 → ~23/60 (5% → ~38%)**. That projection is arithmetic on
already-collected verification results, not a claim about a future experiment;
it must be confirmed by running M2B as its own ablation.

Loop detection should be **kept** (it is cheap, reduces tokens ~11%, and
provides the stall signal M2B can trigger on) but it is not sufficient alone.

## 7. Files changed for M2A

- `smallcoder/recovery/loop_detector.py` (new) — fingerprints, exact-repetition
  and no-progress-cycle detection
- `smallcoder/agent/runtime.py` — loop check per step, bounded strategy-reset
  intervention preserving discoveries, step-count fix under history compaction
- `smallcoder/agent/state.py` — files_read / error_signatures / loop counters
- `smallcoder/config.py` — `loop_detector` + threshold settings, `_env_bool`
- `smallcoder/cli.py` — `--loop-detector/--no-loop-detector` ablation flag
- `tests/test_loop_detector.py` (new) — 15 unit + integration tests
- `evals/fixtures/{pagination,configload,storecart,csvparse}/` (new) — 4 fixtures
- `evals/tasks/*.json` (new) — 5 task specs with reference fixes
- `evals/run_benchmark.py` (new) — ablation runner with outage resilience
- `pyproject.toml` — exclude fixture projects from lint

## Reproducibility

`python -m evals.run_benchmark --model MODEL --loop-detector on|off --trials 3
--out results/benchmarks/m2a/rows.jsonl`. Raw rows:
`results/benchmarks/m2a/rows.jsonl` (60). Trajectories under `results/runs/`
(not committed). One infrastructure note: an initial sweep lost 45 runs to a
local network outage (recorded as `model_error`); those rows were discarded,
the runner was hardened to wait for connectivity and retry once, and the
affected cells were re-run in full.
