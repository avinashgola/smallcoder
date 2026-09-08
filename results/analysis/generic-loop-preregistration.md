# Preregistration: generic agent-loop control study

**Status: frozen before any model call.** Implementation commit `9f1c078`.
Nothing below may change once the first run is recorded.

## Why this study exists

SmallCoder's thesis is that a coding agent built on a small model does better
when the *runtime* owns stepping, verification, recovery and budgets, rather
than the model. Every result published so far — M2A, M2B, M3, and the M3
generalization study — compares SmallCoder to SmallCoder with a flag switched
off. None of them compares it to an agent without a runtime.

That matters because even the fully-ablated arm is not a generic agent. It
still has structured JSON actions with validation and a reformat retry,
exact-unique search/replace edits, a bounded stateless prompt rebuilt each
step, and completion gated behind deterministic verification. The central
claim has therefore never been tested against its own null.

This study builds that control and measures it.

## Honest labelling — this is weaker than the M3 standard

> This is a **prospective preregistration of the control arms and the analysis
> plan**. It is *not* the standard the M3 generalization study met. There, the
> task suite was authored and committed before any model had seen it. Here, the
> comparator's per-task outcomes are **already published**: the designer knew,
> at design time, arm A's and arm B's per-task solve counts, completion modes
> and secondary means from `m3-generalization-results.md`. The comparator arm is
> re-run concurrently so the *data* are fresh, but the *design* was chosen with
> that knowledge. Every claim in the final report must be read in that light.

## Frozen design

- **Runtime under test:** `smallcoder/` at commit `d50b1aa`, unchanged.
- **Control implementation:** `evals/generic_loop.py` at commit `9f1c078`.
- **Suite:** the 12 frozen tasks in `evals/m3_generalization/tasks/`, reused
  without modification.
- **Models:** `llama3.1:latest` and `qwen2.5-coder:7b`, at the digests recorded
  in `results/benchmarks/m3_generalization/meta.json`. The scheduler
  **hard-aborts** if either digest or the Ollama version has drifted, and
  publishes the check result either way. (`llama3.1:latest` is a moving tag.)
- **Size:** 12 tasks × 5 trials × 2 models × 3 arms = **360 runs.**
- **Schedule:** seed `20260908`; two model blocks; within a block the 60
  task/trial pairs shuffled deterministically; within each pair the three arms
  run in seeded random order and stay **adjacent**, so all three see the same
  server conditions. Plan fingerprint
  `0f76e14da21a9176ab8068ed3b00477a3088bca7ac927df42e8fcb4f0a08da93`.

### Arms

| arm | `config` | description |
| --- | --- | --- |
| **S** | `smallcoder-A` | The treatment, tool-matched: loop detection on, stall verification on, path feedback **off**. Chosen over the shipped default because path feedback lives *inside* the tools, so "identical tool implementations" is only satisfiable at `path_feedback=False`. Arm B is reported as a secondary against frozen rows. |
| **G** | `generic` | The control. Same model, tools, action schema, validation, reformat retry, fixtures, settings and command allowlist. The model owns context (accumulating transcript), stopping (`finish` accepted at face value), and recovery (none). |
| **GC** | `generic+completion` | Decomposition cell: the control plus SmallCoder's completion machinery only (verification-gated `finish` and stall-triggered verification), and nothing else. |

### Held constant, and verified by test

Model and tag; temperature 0.2; `structured_format="json"`; `num_ctx` =
`context_limit` = 12000; `max_steps` = 30; `max_tool_output_chars` = 4000 and
both truncation layers; the four tool implementations; the command allowlist;
the JSON action schema, `parse_action`, and exactly one reformat retry;
`MAX_CONSECUTIVE_OUTPUT_FAILURES` = 3; the twelve fixtures; the fresh temp-copy
git baseline per trial; `verify()` and its inputs; and the turn-1 user message.

### The one prompt difference, and why it is honest

The control's system prompt is SmallCoder's with exactly one sentence deleted:

```
- 4. Use finish only when the fix is applied and tests pass. Verification runs automatically.
+ 4. Use finish only when the fix is applied and tests pass.
```

That sentence asserts a property of the runtime. In the control nothing
verifies, so leaving it would tell the baseline a safety net exists that does
not — lowering the cost of a premature `finish` and manufacturing the very
overclaim metric this study reports. Nothing is added in compensation: rule 3
already says "After editing, run the tests to confirm the fix." Adding more
would be new instruction given only to the control.

- SmallCoder prompt SHA-256: `97a91e613bbe8fe0593fee9e76f91927fc9a9fb67ce46f2f946f9ca900524c85`
- Generic prompt SHA-256: `fa8a934c93a2e980843e37e0834e96ad359cc306b05e6111dc214f257e691e90`

Neither prompt states the *consequence* of `finish`. That silence is symmetric
and deliberate.

### Context-overflow policy

Client-side **hard stop, no repair**. Before each call, estimate tokens as
`ceil(total_chars / 3.5)`; if that exceeds `context_limit − 512`, the run ends
with `stop_reason="context_overflow"` and is scored post-hoc like any other.
Nothing is dropped, summarized or reordered.

This is a deliberate choice, not a neutral default. Evicting oldest messages
*is* context management — the capability under test — and would import the
treatment into the control. Letting the server truncate would hand the policy
to undocumented, version-dependent behaviour.

**Stated in advance:** this suite almost certainly cannot exercise overflow.
Reconstructing the accumulating transcript over the 240 frozen runs gives a
maximum well inside a 12000-token (~45k char) window, and SmallCoder's own
prompt budget never bound either — its eviction loop fired zero times in 5,668
recorded model calls. **A near-zero overflow count is a fact about these
fixtures, not evidence about context engineering, and will be reported as
such.** What the context factor actually varies here is *fidelity*: SmallCoder
compresses all but the last three observations to one-line summaries.

## This is a package comparison

> SmallCoder as an integrated runtime versus a generic single-model loop,
> holding model, tools, action schema, fixtures, settings and scoring constant.
> At least fifteen behaviours differ simultaneously. **This establishes whether
> the package helps, not which part of it does.** The single decomposition
> performed is the `generic+completion` arm.

## Predeclared outcomes

**Primary (confirmatory).** `verified_final`: the deterministic `verify()`
pipeline run at the run's own stopping point. One definition, applied
identically to all three arms. Reported per model, **never pooled**.

**Secondary (preregistered).**

- `verified_checkpoint` — anytime scoring at *matched* checkpoints. Replays
  SmallCoder's own gating (tree changed, ≥ `stall_check_interval` steps since
  the last check, diff hash moved) over per-step snapshots, so the control gets
  neither more nor fewer sampling opportunities than the treatment. **This
  addresses the study's most serious confound:** SmallCoder stops at its first
  green checkpoint, so its solve rate is an optimal-stopping maximum, and
  scoring the control only at step 30 would manufacture a gap.
- `generic+completion` versus each neighbour.
- `generic` versus the frozen arm B.
- Drift check: fresh `smallcoder-A` versus frozen arm A (22/60 llama, 16/60
  qwen). If the fresh rate falls inside the frozen study's per-model
  task-cluster bootstrap interval, frozen-row comparisons are licensed and a
  reproducibility result is reported; if not, **every frozen-row comparison is
  dropped**.

**Exploratory** (report raw counts; see the interpretation rules below):
`claimed_success`, `overclaim`, `silent_success`, `delivered_success`,
`verified_ever`, `context_overflow`, `edits_ok` / `edits_failed`,
`commands_run`, `gt_read`, `tampered`.

**Not comparable across arms, and will not be compared.** `tokens_in` is
Ollama's `prompt_eval_count`, which is KV-cache dependent and deflates an
append-only transcript far more than a rebuilt prompt; cost is reported as
client-side `chars_sent_total` / `peak_context_chars` instead. Per-run
`duration_s` bundles SmallCoder's per-step git subprocesses, its mid-run pytest
runs, and its early stop; it is reported conditioned on outcome, never as a
bare "N× faster" headline.

## Statistical analysis

Consistent with the M3 generalization standard:

- The **task is the unit of generalization** — 12 clusters, per model, never
  pooled.
- Primary statistic: paired per-task difference
  `d_t = solve_rate_t(smallcoder-A) − solve_rate_t(generic)`, each out of 5
  trials. Point estimate `mean(d_t)`; 95% CI from the task-cluster bootstrap
  imported verbatim from `evals/analyze_m3_generalization.py`, 10,000
  resamples, fresh RNG per model/outcome.
- One **confirmatory test per model**: a two-sided sign test on the 12 `d_t`.
  Its floor is p ≈ 0.00049 (all twelve in one direction).
- Run-level Fisher tests are **descriptive only**, labelled as treating
  clustered runs as independent observations. Any pooled "combined" row emitted
  by `evals.analyze_rows` is excluded.

### Power, stated before running

Powered only to detect roughly a **halving** of the solve rate. Against the
observed per-task rates, power is approximately 0.37 (llama) / 0.31 (qwen) for
a 25% relative drop, 0.82 / 0.66 for 50%, and ≥0.96 for 75%. Worse, arm B is
0/5 on four llama tasks and five qwen tasks; those clusters cannot produce a
positive paired difference, so the effective cluster count is 7–8, not 12.
**A non-significant result is inconclusive, never "no difference."**

### Interpretation rules, fixed in advance

1. If an arm produces **fewer than 10 `finish` events per model**, report raw
   counts and decline to compute a rate difference. (Expected: only 5 of the
   240 frozen runs ever emitted `finish`.)
2. A zero `overclaim` count is **evidence about finish rate, not about
   calibration**. `overclaim` must never be the headline: the treatment's is
   zero by construction.
3. **qwen is predicted to be a degenerate cell.** In the frozen study it issued
   a `run_command` in 5/120 runs and obtained an exit-0 command in 0/120. Its
   `claimed_success` ceiling is therefore near zero. This is preregistered as a
   prediction; the cell will be reported as a documented degenerate case and
   will not carry the primary contrast alone.
4. The 0/161 pass rate among frozen `max_steps` runs is **survival-conditioned**
   (runs that passed a checkpoint were removed from that population by the
   runtime) and is **not** transportable to the control. It is not preregistered
   as a prediction.

### Integrity rule

Any run whose `files_changed` intersects the fixture's tests or `conftest.py`
is marked `tampered` and counted as **not solved**, regardless of verification.
`verify()` runs the repository's own pytest, so the oracle is forgeable. Applied
retroactively and symmetrically to all arms; counts reported per arm. (In the
frozen sweep exactly 3 of 240 rows touched test files, all of which already
failed, so adopting this rule costs nothing and closes a real hole.)

## What would count as what

**(a) Falsifies the thesis.** For **both** models, the bootstrap 95% CI on
`d_t` has an upper bound below a minimum meaningful effect of **+0.05**, and the
sign test is non-significant. Reading: the runtime spends steps, tokens, git
subprocesses, mid-run pytest and ~550 lines of state machine and buys no task
success over a plain accumulating loop with the same tools. **This will be
reported as prominently as a win.**

**(b) Narrows the thesis — predicted as the most likely outcome.** SmallCoder
wins on `verified_final`, but `verified_checkpoint(generic)` ≈
`verified_final(smallcoder-A)`: the control reaches equally correct working
trees and simply never notices. Then the contribution is not "make the model do
less, make the system smarter" but the far narrower "attach a deterministic
verifier to any loop and stop it when the tests go green," and the broader
framing must be retracted. **This is stated as the expected result in advance,
because 39 of 41 arm-B successes were runtime-rescued and only 2 were
model-initiated.** The `generic+completion` arm sharpens it: if it matches
`smallcoder-A`, then context policy and recovery contribute nothing here.

**(c) Null / uninconclusive.** CIs spanning zero on both models with per-task
differences scattered in both directions. Given 12 clusters and 4–5 floor tasks
per model, this study cannot distinguish a null from a modest true effect, and
a null will be reported as inconclusive rather than as evidence of no effect.

## Conduct rules (binding)

1. No task, fixture, runtime, prompt, threshold or control-implementation change
   after the first recorded run. A defect discovered mid-sweep stops the sweep;
   the study restarts from a corrected, re-frozen implementation and the restart
   is reported.
2. No interim result analysis, and no stopping, extending or re-running based on
   observed performance. The runner's built-in infrastructure handling (wait for
   the server, one retry on `model_error`) is the only permitted retry.
3. Every infrastructure failure, aborted cell, retry and excluded row is
   reported.
4. Raw rows are committed only after a leak scan (no endpoints, hosts,
   credentials or `.env` values). Trajectories and snapshots under
   `results/runs/` stay uncommitted.
5. The analysis reports **every** planned outcome, whether favorable or not,
   including outcome (a).
