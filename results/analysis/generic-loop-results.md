# Generic agent-loop control study: results

**Preregistered** in [`generic-loop-preregistration.md`](generic-loop-preregistration.md),
frozen at commit `827a717` before any model call. 360 runs: 12 tasks × 5 trials
× 2 models × 3 arms. Every predeclared outcome is reported.

---

## Headline

**A generic agent loop, given the same model and the same tools, matches
SmallCoder.** On the primary endpoint neither model shows a detectable
advantage for the runtime:

| model | `smallcoder-A` | `generic` | paired per-task difference (95% CI) | sign test |
| --- | --- | --- | --- | --- |
| llama3.1:latest | 23/60 | **24/60** | −0.017 [−0.167, +0.117] | p = 1.0 |
| qwen2.5-coder:7b | 22/60 | 20/60 | +0.033 [−0.150, +0.217] | p = 0.55 |

By the preregistered criteria the verdict is **(c) inconclusive**: the intervals
span zero, but their upper bounds (+0.117, +0.217) exceed the minimum meaningful
effect of +0.05, so this study also cannot *rule out* a real advantage. As
preregistered: **a non-significant result here is inconclusive, never "no
difference."** What it is not is evidence of a win.

And a second finding that matters more than the first:

**The premise M2B was built on does not survive a control.** SmallCoder's
records say small models essentially never request completion — 2/60 for llama,
0/60 for qwen. The *same models*, on the *same tasks*, in a loop without the
runtime, call `finish` constantly and are usually right to:

| model | arm | called `finish` | claim was correct |
| --- | --- | --- | --- |
| llama3.1 | `smallcoder-A` | 2/60 | 2 |
| llama3.1 | `generic` | **43/60** | **24** |
| qwen2.5-coder | `smallcoder-A` | 0/60 | 0 |
| qwen2.5-coder | `generic` | **22/60** | **20** |

"Small models cannot judge when they are done" was measured entirely inside the
harness built on that assumption.

---

## What was run

Three arms, all interleaved — for each (model, task, trial) the three runs are
adjacent in seeded random order, so all three see the same server conditions.

- **S — `smallcoder-A`**: the treatment, tool-matched (loop detection on, stall
  verification on, path feedback off).
- **G — `generic`**: same model, tools, action schema, validation, reformat
  retry, fixtures, settings, allowlist. The model owns context (accumulating
  transcript), stopping (`finish` at face value), and recovery (none).
- **GC — `generic+completion`**: the control plus SmallCoder's completion
  machinery only.

The prompts differ by exactly one deleted sentence, "Verification runs
automatically.", which is true of the runtime and false in the control. The
environment guard verified both model digests and the Ollama version were
identical to the M3 study before the first run.

## Primary endpoint — `verified_final`

The deterministic `verify()` pipeline at each run's own stopping point, one
definition for all three arms, integrity rule included.

| arm | llama3.1 | qwen2.5-coder |
| --- | --- | --- |
| `smallcoder-A` | 23/60 | 22/60 |
| `generic` | 24/60 | 20/60 |
| `generic+completion` | 19/60 | 14/60 |

**Adding the completion machinery to the generic loop made it worse** — llama
24 → 19, qwen 20 → 14. The verification gate rejects a premature `finish` and
sends the model back around; it then churns and, often, ends in a worse state
than it had. For qwen the effect on behaviour is stark: `finish` claims collapse
from 22/60 to 3/60 once the gate can reject them.

## The completion-machinery question, answered directly

The obvious objection to the headline is that SmallCoder stops at its first
green checkpoint while the control is scored at its terminal state, so the
control's number is not comparable. The study was designed around that
objection, and it does not survive:

> **Would SmallCoder's completion machinery have completed the control's runs?**
> For arm S this is exactly its recorded success (it had both pathways: a gated
> `finish` at any step, plus stall checks). The control's analogue is a passing
> matched checkpoint *or* a correct accepted `finish`.
>
> | model | `smallcoder-A` | `generic` composite |
> | --- | --- | --- |
> | llama3.1 | 23/60 | **24/60** |
> | qwen2.5-coder | 22/60 | 20/60 |

Dead even. The `generic+completion` arm tests the same thing empirically, by
actually giving the control both pathways, and lands *lower* than either.

**`verified_checkpoint` in isolation is not evidence and is not used as such.**
It reads +0.283 for llama (sign test p = 0.016) in SmallCoder's favour, but that
is an artifact: for arm S it includes the finish pathway, while for the control
it replays only the stall pathway, which cannot fire before step 5. The control
finishes early — median finish step 11, and 10 of 43 llama finishes land before
step 5 — so the replay structurally cannot see those runs. It is reported for
completeness and excluded from the conclusion.

`verified_ever` is **not measured** for arm S: it requires per-step snapshots,
and the treatment runs the unmodified runtime, which takes none. It is reported
for the control arms only and never differenced against the treatment.

## Why SmallCoder's records showed no model-initiated completion

Two mechanisms, and this study can quantify one of them:

**Right-censoring.** SmallCoder's stall verification ends runs before the model
gets to decide. llama's median rescue step is **5** — the earliest a stall check
can fire — while the control's median `finish` step is **11**. The runtime is
routinely ending the run roughly six steps before the model would have called
it. Of arm S's llama successes, 21 are runtime-rescued and 2 model-initiated.

**The prompt.** SmallCoder's rule 4 tells the model "Verification runs
automatically," which plausibly suppresses explicit completion. Separating this
from right-censoring needs the B-prime cell (SmallCoder with the control's
prompt), which was specified as Tier 3 and **not run**. Until it is, the two
explanations are confounded and neither is claimed alone.

Either way, the previously reported framing — that these models produce correct
fixes but cannot recognise them — is not supported once a control exists. They
recognise them fine; SmallCoder's records could not show it.

## Secondary and exploratory outcomes

| arm | claimed | overclaim | silent success | delivered | tampered | ctx overflow |
| --- | --- | --- | --- | --- | --- | --- |
| llama `smallcoder-A` | 2 | 0* | 21 | 2 | 1 | 0 |
| llama `generic` | 43 | 19 | 0 | 24 | 2 | 0 |
| llama `generic+completion` | 35 | 20 | 5 | 15 | 2 | 0 |
| qwen `smallcoder-A` | 0 | 0* | 23 | 0 | 1 | 0 |
| qwen `generic` | 22 | 2 | 0 | 20 | 2 | 1 |
| qwen `generic+completion` | 3 | 0* | 12 | 3 | 1 | 1 |

`*` **zero by construction, not by calibration.** The runtime gates `finish`
behind verification, so a treatment overclaim is impossible. As preregistered,
this is evidence about finish rate, not about accuracy.

The two models differ sharply in calibration: qwen's claims are almost always
right (20 correct of 22), llama's are right about half the time (24 of 43).

**Context overflow: 2 runs of 240 control runs**, exactly as predicted in
advance. This suite cannot exercise context management, and that near-zero count
is a fact about 3–6 file fixtures, not evidence about context engineering.

**Cost.** Reported, never differenced — `tokens_in` is cache-dependent and
`duration_s` bundles SmallCoder's early stop and per-step git/pytest work.
Directionally, the control used *fewer* steps (llama 16.8 vs 22.4).

## Drift check

| model | fresh `smallcoder-A` | frozen M3 arm A |
| --- | --- | --- |
| llama3.1 | 23/60 | 22/60 |
| qwen2.5-coder | 22/60 | 16/60 |

llama reproduces closely — a genuine reproducibility result three weeks apart on
the same digests. **qwen does not** (16 → 22). Per the preregistration, every
frozen-row comparison for qwen is therefore **dropped**. It also says something
uncomfortable and useful: run-to-run variation on this suite is of the same
order as the effects being chased, which is the clearest argument that this
design is underpowered.

## What this means for the project

The M2A/M2B/M3 ablations are not retracted — they are valid *within-harness*
comparisons and their numbers stand. What is retracted is the **interpretation**:

- "M2B took a small model from 10% to 60%" remains true of SmallCoder-with-stall
  versus SmallCoder-without-stall. It does **not** show that SmallCoder beats an
  agent without a runtime, and this study finds it does not.
- The thesis "make the model do less, make the system smarter" is **not
  supported** by this experiment. On these tasks, with these models, the loop
  that asks the model to do more does just as well.
- The specific claim that small models cannot judge completion is **withdrawn**.

The honest summary of the whole project becomes: *a deterministic runtime makes
a small-model agent's successes verifiable and reproducible, and its own
ablations quantify what each mechanism contributes inside that runtime — but on
this suite it does not outperform a competent generic loop using the same model
and tools.*

## Limitations

1. **Underpowered by design, and stated in advance.** Twelve task clusters, with
   four to five at a 0/5 floor per model; powered only to detect roughly a
   halving. The drift check shows within-arm variance of similar size.
2. **Package comparison.** At least fifteen behaviours differ between S and G
   simultaneously. This establishes whether the package helps, not which part
   does. The single decomposition run is the GC arm.
3. **Narrow population.** 12 small single-defect Python fixtures. No claim about
   coding-agent performance in general, and in particular nothing here transfers
   to large repositories, where SmallCoder's bounded prompt may matter far more.
4. **Weaker preregistration than M3.** The comparator's per-task outcomes were
   already published and known at design time; only the data are fresh.
5. **Tier 3 not run.** Without B-prime, the prompt and right-censoring
   explanations for the finish-rate gap remain confounded.

## Disclosures (conduct rule 3)

1. **One transient `model_error`** at schedule index 63, retried once and
   succeeded — the only permitted retry mechanism, used once. No other
   infrastructure failures; no aborted cells; no duplicate rows (360 unique
   keys, so no dedupe was needed).
2. **Two analysis-tooling defects found after the sweep completed**, both fixed
   before any number here was produced, neither touching a task, fixture,
   runtime, prompt, threshold or the control implementation, and neither
   changing a frozen endpoint definition:
   - The anytime replay re-snapshotted an already-edited tree as its baseline,
     so `changed_since` returned nothing and every snapshot scored unverified.
     This **understated the control arm** on the study's own fairness metric.
     Caught because `verified_final = 1` with `verified_ever = 0` is impossible.
   - The analyzer scored an *unmeasured* endpoint as zero, reporting
     `verified_ever` as 0/60 for the treatment arm and producing a meaningless
     −0.400 comparison. Unmeasured endpoints are now reported as such and never
     differenced.
   Both are covered by regression tests.
3. **9 runs were marked `tampered`** (edited the fixture's own tests) and count
   as failures under the integrity rule; 1 recorded success changed as a result.
   Applied symmetrically to all arms.
4. `verified_ever` is not computable for the treatment arm, as described above.

## Reproducibility

```bash
python -m evals.run_generic_study --validate
python -m evals.replay_verify   --rows results/benchmarks/generic_loop/rows.jsonl \
    --out results/benchmarks/generic_loop/rows_annotated.jsonl
python -m evals.normalize_arms  --rows results/benchmarks/generic_loop/rows_annotated.jsonl \
    --out results/benchmarks/generic_loop/rows_final.jsonl
python -m evals.analyze_generic_study --rows results/benchmarks/generic_loop/rows_final.jsonl
```

Tracked: `plan.json` (fingerprinted 360-entry schedule), `rows.jsonl`,
`rows_final.jsonl`, `meta.json` (digests and both prompt hashes). The bootstrap
seed is fixed at 20260908 in code; identical inputs give byte-identical output.
The anytime endpoints derive from per-step snapshots under `results/runs/`,
which stay uncommitted — `rows_final.jsonl` publishes the derived booleans so
the conclusions remain checkable without them.
