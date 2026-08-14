# Residual failure analysis: held-out M2B arm

**Date:** 2026-08-15
**Scope:** all 19 failed runs in the held-out M2A+M2B arm (48 runs total).
**Runtime state:** frozen at `48882f2`; `smallcoder/` verified byte-identical
before and after this analysis. Nothing was modified, tuned, or re-run.

## Methodology

Every failed run's `trajectory.jsonl` and `result.json` were parsed
programmatically to extract: files read/edited, whether the ground-truth file
was read and edited, whether the reference fix text ever appeared in a
successful edit, verification events, error signatures, edit churn, repeated
actions, loop detections, and the final working-tree diff. Classification was
evidence-driven (rules over extracted signals), then every ambiguous case was
hand-inspected against its actual diff and action sequence and corrected —
`856c` was reclassified from LOCALIZATION to MULTI_FILE_CONTEXT after
confirming it read the file whose import names the defect file. Nothing is
labelled MODEL_CAPABILITY by default; each label cites a concrete mechanism.

## Aggregate failure distribution (n = 19)

| Primary failure | Count | % of failures |
| --- | --- | --- |
| TOOL_MISINTERPRETATION (path hallucination, no recovery) | 9 | 47% |
| BAD_EDIT (wrong implementation) | 7 | 37% |
| MULTI_FILE_CONTEXT | 1 | 5% |
| LOCALIZATION (symbol hallucination) | 1 | 5% |
| EDIT_CHURN (correct fix destroyed) | 1 | 5% |

| Concrete mechanism | Count |
| --- | --- |
| Requested a non-existent path (right basename, invented directory) and never recovered | 9 |
| Read the right file, produced a semantically wrong fix (usually with anchor churn) | 7 |
| Searched repeatedly for a symbol that does not exist | 1 |
| Read the symptom file, never followed its import to the defect file | 1 |
| Applied the correct fix, then destroyed it | 1 |

### Key rates

| Question | Result |
| --- | --- |
| Correct file **read** | 9/19 = 47% |
| Correct file **edited** | 8/19 = 42% |
| All necessary files read | 9/19 = 47% |
| Correct patch present at any point | 1/19 = 5% |
| Verification ever passed | 0/19 = 0% |
| Runtime could theoretically have rescued (patch existed) | 1/19 = 5% |
| Required genuinely better code reasoning | 7/19 = 37% |
| Made no successful edit at all | 10/19 = 53% |

## Part 3 — Localization vs reasoning (A–F)

| Bucket | Count | % | Meaning |
| --- | --- | --- | --- |
| A | 1 | 5% | Never found the relevant code |
| B | 1 | 5% | Found code, lacked supporting context |
| C | 0 | 0% | Context sufficient, misunderstood the bug |
| D | 7 | 37% | Understood the bug, wrong implementation |
| E | 1 | 5% | Correct implementation, later destroyed |
| **F** | **9** | **47%** | **Blocked by tool/runtime interaction** |

**The single most important finding:** the 9 F-bucket runs are *not*
localization failures. In every case the model named the **correct basename**
but invented a directory prefix — `src/tempconv.py`, `src/calendar_utils.py`,
`src/jsonflat.py`, `src/logparse.py` — while the correct root-level path was
listed in the "Repository files" block of **every** prompt. The runtime replied
`ERROR: File not found: src/calendar_utils.py` up to 28 times in a single run
and the model never adjusted. 270 `File not found` errors occurred across arm
B, concentrated in 12 runs.

A repository localizer that *ranks candidate files* cannot fix this: the model
already selected the right file. What failed is path resolution and recovery
from an unambiguous tool error.

## Part 4 — By model

| | llama3.1 8B | qwen2.5-coder 7B |
| --- | --- | --- |
| Failures | 13 | 6 |
| Path hallucination (F) | **9** | 0 |
| Wrong implementation (D) | 4 | 3 |
| Localization / multi-file (A/B) | 0 | 2 |
| Correct fix destroyed (E) | 0 | 1 |

- **llama-specific:** path hallucination is exclusively llama (9/13 of its
  failures, 0 for qwen). llama's 0/3 on `tempconv` and 0/3 on `leapyear` are
  *entirely* explained by never once opening the file — we have no evidence
  llama cannot fix those bugs, only that it never saw the code.
- **qwen-specific:** symbol hallucination in `search_code`, following the
  issue's wording rather than the repo map (`calculate_available_units`, a
  function that does not exist), and edit churn destroying a correct fix.
- **Shared:** wrong implementation after correctly reading the file (llama 4,
  qwen 3) and edit-anchor churn (`old_text not found`, 8/19 failures).

## Part 5 — By task (arm B, 6 runs each)

| task | solved | failure buckets | GT file | multi-file? | had enough evidence? |
| --- | --- | --- | --- | --- | --- |
| usergroups | 6/6 | — | auth/permissions.py | yes | yes |
| inventory | 4/6 | A 1, B 1 | warehouse/stock.py | yes | yes — `report.py` imports it |
| logparse | 4/6 | F 1, D 1 | logparse.py | no | yes |
| textstats | 4/6 | D 1, E 1 | textstats.py | no | yes |
| leapyear | 3/6 | F 3 | calendar_utils.py | no | yes — never opened |
| ratelimit | 3/6 | D 3 | ratelimit.py | no | yes |
| tempconv | 3/6 | F 3 | tempconv.py | no | yes — never opened |
| jsonflat | 2/6 | F 2, D 2 | jsonflat.py | no | yes |

**No task was zero-solve across both models**, so no fixture is inherently
unsolvable by this model class. Per-model zero-solve cells: llama on
`tempconv`, `leapyear`, `jsonflat`, `ratelimit`.

- `tempconv` / `leapyear` (llama 0/3): missing step was **opening the file** —
  pure path hallucination, no reasoning was ever attempted.
- `ratelimit` (llama 0/3): missing step was **understanding aliasing**. llama
  read the file and wrote `if overrides is None:` followed by
  `if overrides is not None: limits.update(overrides)` — incoherent. Genuine
  reasoning failure.
- `jsonflat` (llama 0/3): 2 runs never opened the file; 1 read it and removed
  `and value` instead of fixing `items[key]` → `items[full_key]`.
- **Repository size was not a blocker:** `textstats` (8 distractor files) and
  `usergroups` (4 unrelated modules) had the *highest* solve rates.

## Representative trajectories

**F — path hallucination (`e44a`, llama/leapyear).** 28 × `read_file
src/calendar_utils.py` → `File not found`, interleaved with 2 `python -c
'print(os.getcwd())'` probes. 21 loop detections, 2 interventions; after each
strategy-reset instruction the model resumed the identical call. 0 files read,
0 edits, 0 stall checks. The correct path `calendar_utils.py` was in every
prompt.

**D — wrong implementation (`15f3`, llama/ratelimit).** Read `ratelimit.py`,
then produced `if overrides is None:` / `if overrides is not None:
limits.update(overrides)`. Never touched the aliasing line
(`limits = DEFAULTS`). 9 `old_text not found` errors as it thrashed.

**D — wrong implementation (`a7b1`, qwen/logparse).** Changed
`split("|")` → `split('\\|')`, i.e. regex-escaping a literal separator —
a misunderstanding of `str.split`, not a mechanical error.

**E — correct fix destroyed (`a163`, qwen/textstats).** Applied the exact
reference fix, then continued editing; 9 edit-churn operations and 7
`old_text not found` errors later the tree no longer verified. 6 stall checks
fired, none while the tree was green.

**B — defect file never reached (`856c`, qwen/inventory).** Searched 5× for
`calculate_available_units` (does not exist), then read and edited
`warehouse/report.py` — whose line 3 reads
`from warehouse.stock import available`. It never followed that import to the
actual defect.

## Part 7 — Candidate M3 interventions

**Ranked top 3:**

1. **Path-resolution feedback on failed file references** (variant of
   "edit-tool feedback"). When `read_file`/`edit_file` gets a non-existent
   path, the runtime resolves the basename against the repo map and returns
   `File not found: src/tempconv.py. Did you mean: tempconv.py?` — or resolves
   it outright. Addresses **9/19 failures (47%)**. Fully deterministic,
   runtime-owned, needs no model capability, ~30 lines, one ablation flag.
2. **Edit-anchor assistance / patch protection.** Better `old_text not found`
   feedback plus "already applied" detection. Appears in 8/19 failures — but
   in 7 of those the underlying fix was *semantically wrong anyway*, so
   expected yield is ~1 run (the E case). High frequency, low yield.
3. **Multi-file context routing (import following).** Addresses the single B
   case. Multi-file tasks were already the best-performing category
   (`usergroups` 6/6, `inventory` 4/6), so the evidence does not support it.

**Recommended: #1 — path-resolution feedback.**

**Rejected and why:**
- **Repository localization (A):** the evidence contradicts it. Models chose
  the correct file in 17/19 failures; only 1 failure (`0094`) is a true
  "never identified the code" case. A ranker would not have changed any of the
  9 dominant failures.
- **Context selection / multi-file routing (B):** 1/19 failures. Multi-file
  tasks are already the strongest category.
- **Structured planning (C):** no failure in the data traces to absent
  planning; failures are execution- and comprehension-level.
- **Test/tool-result interpretation broadly (E):** overlaps the recommendation
  but is far larger in scope; the path case is the isolatable, high-yield core
  of it.
- **Better reasoning:** the 7 D-bucket failures are genuine model-capability
  limits and are *not* runtime-fixable without changing the model.

## Part 8 — Evidence-based impact bound

- 19 failures remain in arm B (48 runs).
- 9 are caused primarily by path hallucination with no recovery.
- **Maximum directly addressable population ≈ 9/48 runs (19% of arm B).**

This is an upper bound, not a projection. Resolving the path only guarantees
the model *reaches* the code; it must still fix the bug. The relevant
conditional evidence from this same arm:

| model | runs that read the GT file | solved | conditional solve rate |
| --- | --- | --- | --- |
| llama3.1 8B | 16/24 | 11 | 69% |
| qwen2.5-coder 7B | 19/24 | 15 | 79% |

Applying llama's 69% conditional rate to its 9 blocked runs suggests roughly
**5–6 additional solves**, with the caveat that this rate is measured on runs
that got past the path step and may be optimistic (selection bias: reading the
file correlates with an otherwise on-track run). No solve-rate projection is
claimed here; the ablation must measure it.

Note the population is **model-skewed**: all 9 are llama runs. On the two
tested models this intervention would help llama substantially and qwen
approximately not at all. That is a real limitation, stated rather than hidden.

## Expected measurable target for the next ablation

- **Primary metric:** solve rate (arm B held-out baseline: 29/48 = 60%).
- **Diagnostic metric 1:** share of runs that successfully read the
  ground-truth file — baseline **35/48 = 73%** overall, **16/24 = 67%** for
  llama. This is the metric the intervention acts on directly.
- **Diagnostic metric 2:** `File not found` errors per run — baseline 270
  across 48 runs, concentrated in 12 runs.
- **Design:** M2B-frozen vs M2B + path-resolution feedback, single ablation
  flag, same 8 held-out tasks (plus the 5 design tasks for breadth), both
  models, 3 trials — 96 runs per suite, loop detection and stall verification
  enabled in both arms.

## Reproducibility

Runtime commit `48882f2` (frozen, unmodified) · analysis inputs
`results/benchmarks/heldout/rows.jsonl` (96 runs, 24/cell after excluding the
documented orphan row) and the corresponding trajectories under
`results/runs/` (gitignored; they contain host strings from the outage).
