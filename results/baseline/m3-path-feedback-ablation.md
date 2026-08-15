# Milestone 3 ablation: deterministic path-resolution feedback

**Date:** 2026-08-15
**Design:** 2 models × 2 arms × 8 tasks × 3 trials = **96 runs**, all
at commit `d50b1aa`. Arm A = frozen M2B (loop detection ON, stall verification
ON, path feedback OFF). Arm B = identical plus path feedback ON. Path feedback
is the only variable; no prompt, planning, context, stall-verification,
loop-threshold, or benchmark-task change was made.

**Suite provenance — read before interpreting.** The eight tasks in
`evals/heldout/tasks` were authored after the M2B freeze and are a genuine
held-out suite *for M2B*. For M3 they are **not** held out: M3 was designed
from the residual-failure analysis of M2B's failures on these very tasks
(`results/analysis/residual-failures-m2b.md`), so this study reuses the suite
as M3's **evaluation/design set**. The A/B comparison is still a valid
controlled measurement of the mechanism's causal effect on these tasks — both
arms ran fresh at the same commit with one flag flipped — but it is not
independent evidence that M3 generalizes beyond them. An independently
authored M3 generalization suite, frozen after the M3 implementation, remains
future work.

## Implementation

`smallcoder/tools/path_suggest.py` — shared by `read_file` and `edit_file`.
On a non-existent repository-relative path it matches the requested basename
against real repository files: exact basename, then case-insensitive basename,
disambiguated by the longest matching trailing path suffix. One candidate →
`Did you mean: <path>`; several → `Possible matches:` listing all; none → the
ordinary error, unchanged. The tool never redirects the operation — the model
must retry explicitly, so behaviour stays transparent and auditable. Sandbox
violations (absolute paths, `..`, symlink escapes, `.git`) are rejected before
the suggestion path is reached and never receive suggestions; candidates are
enumerated by walking the repository, so they are inside the sandbox by
construction.

## Results

| cell | solved | solve rate | GT-file read rate | max_steps | file-not-found (total / per run) | suggestions emitted / followed | steps | tokens in | wall-clock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1 8B — A (off) | 13/24 | 54% | 62% | 46% | 275 / 11.5 | 0 / 0 | 18.2 | 13,637 | 31 s |
| llama3.1 8B — B (**ON**) | **19/24** | **79%** | **100%** | 21% | **55 / 2.3** | 55 / 16 | 11.5 | 10,828 | 22 s |
| qwen2.5-coder 7B — A (off) | 18/24 | 75% | 83% | 25% | 0 / 0 | 0 / 0 | 14.5 | 11,225 | 42 s |
| qwen2.5-coder 7B — B (ON) | 17/24 | 71% | 83% | 29% | 0 / 0 | **0 / 0** | 14.8 | 11,453 | 43 s |
| combined A | 31/48 | 65% | 73% | 35% | 275 / 5.7 | 0 | 16.3 | 12,431 | 36 s |
| combined B | 36/48 | 75% | 92% | 25% | 55 / 1.1 | 55 / 16 | 13.1 | 11,141 | 33 s |

### Statistical notes (Fisher's exact, two-sided)

| comparison | p |
| --- | --- |
| llama GT-file read rate 15/24 → 24/24 | **0.0016** |
| llama solve rate 13/24 → 19/24 | 0.125 |
| qwen solve rate 18/24 → 17/24 | 1.0 |
| combined solve rate 31/48 → 36/48 | 0.374 |

The **mechanism metric moves decisively** (p = 0.0016). The llama solve-rate
gain (+6 runs, +25 pts) is directionally large but **not statistically
significant at n=24**; it should be read as encouraging, not established.

## Model-specific findings — the effect is llama-only, exactly as predicted

**llama3.1 8B.** Ground-truth-file read rate went **62% → 100%**: with
suggestions enabled, *every one of 24 runs* reached the file it needed.
File-not-found errors fell **275 → 55 (−80%)**, steps −37%, prompt tokens
−21%, wall-clock −29%, max_steps rate 46% → 21%. Tasks that were previously
blocked purely by path hallucination flipped completely: `tempconv` 0/3 → 3/3
and `leapyear` 0/3 → 3/3.

**qwen2.5-coder 7B.** **Zero** file-not-found errors in either arm, therefore
**zero suggestions emitted** — the M3 code path never executed for qwen in any
of its 48 runs. Its 18/24 → 17/24 difference is run-to-run stochastic variance
and **cannot be attributed to M3** (p = 1.0); no mechanism was active. This
confirms the residual analysis prediction that path hallucination is
llama-specific among the tested models. M3 delivers no benefit to qwen and, as
implemented, costs it nothing.

## Causal chain

11 arm-B runs emitted at least one suggestion (all llama). Tracing each:

| stage | count |
| --- | --- |
| runs where a suggestion fired | 11 |
| → model subsequently used a suggested path | **11/11** |
| → model then read the ground-truth file | **11/11** |
| → run solved | **8/11** |
| of which completed by runtime verification | 7 |
| of which completed by the model itself | 1 |

The 3 that read the file and still failed are reasoning failures on tasks the
residual analysis already flagged as llama-weak (`jsonflat` ×2, `logparse` ×1)
— llama scores 1/3 on `jsonflat` in *both* arms.

Representative single-suggestion recoveries (`39a2`, `b995`, `d9e5` on
leapyear; `d6a1`, `1a25`, `c490` on tempconv): one `File not found:
src/calendar_utils.py → Did you mean: calendar_utils.py`, the model retried
with the correct path on its very next action, read the file, fixed the bug,
and the run completed — versus 28 repeated failing references and zero files
read in the corresponding arm-A runs.

Two runs (`e65b` 28 suggestions, `446f` 14) show the failure mode persisting:
the model used a suggested path *and* kept re-hallucinating others. Suggestions
reduce path thrash substantially but do not eliminate it.

## Remaining failures (12 in arm B)

- **llama (5):** 3 reasoning failures after successfully reading the file
  (`jsonflat` ×2, `logparse` ×1), plus residual path thrash in 2 jsonflat runs.
- **qwen (7):** untouched by M3 — wrong implementation, edit-anchor churn, and
  the multi-file import case identified in the residual analysis.

## Verdict: keep M3

Cheap (~90 lines behind a flag), zero cost when it does not fire, no sandbox
weakening, and it converts the single largest runtime-fixable failure class for
one of two tested models. The honest framing is: **M3 fixes a model-specific
tool-interaction failure completely (GT-read 62% → 100%, p = 0.0016) and the
resulting solve-rate gain is promising but not yet statistically established.**

## Recommended next step

The residual population is now dominated by **wrong implementations after the
model has read the correct file** — genuine reasoning failures that no runtime
mechanism addressed so far. The two remaining runtime-shaped candidates are
edit-anchor feedback (qwen churn) and multi-file import following (1 case).
Neither is large. A more valuable next experiment is **increasing statistical
power on what already exists** (more trials/tasks) rather than adding a fifth
mechanism, since M2B and M3 both currently rest on n=24 cells.

## Reproducibility

Commit `d50b1aa` · Python 3.12.10 · `llama3.1:latest` (8.0B Q4_K_M),
`qwen2.5-coder:7b` (7.6B Q4_K_M) · context limit 12000 · max steps 30 · stall
interval 5 · loop thresholds 3/6/2 · task suite `evals/heldout/tasks` (held
out for M2B, reused as M3's evaluation/design set — see suite provenance
above) · fresh git baseline per trial. Raw rows:
`results/benchmarks/m3/rows.jsonl` (96). Command:
`python -m evals.run_benchmark --model MODEL --loop-detector on
--stall-verification on --path-feedback on|off --trials 3 --tasks-dir
evals/heldout/tasks --out results/benchmarks/m3/rows.jsonl`.
The original 5-task M2A/M2B design suite was **not** run;
`evals/heldout/tasks` was specified as this study's primary suite.

Row-level tables (cell sizes, solve rates, per-task solves, metric means, and
the Fisher p-values on solve rate) can be recomputed from the tracked rows
alone:

```
python -m evals.analyze_rows results/benchmarks/m3/rows.jsonl --expect-cell-size 24
```

The GT-file read rates, the suggestion → read → solve causal chain, and the
per-run narratives above were derived from `trajectory.jsonl` files under
`results/runs/`, which are gitignored (they can contain endpoint strings from
outages); those claims are not recomputable from `rows.jsonl`.
