# SmallCoder

**A coding-agent runtime optimized for small local LLMs (<12B parameters).**

SmallCoder investigates one question:

> How far can systems engineering push a small language model without fine-tuning it?

## Why small models struggle as coding agents

Generic agent harnesses ask the model to do everything at once: navigate the
repository, plan, manage its own context, pick tools, write code, interpret
errors, decide on retries, and judge when it is done. Frontier models absorb
that load; 7B–12B models drop the ball on several of these at once, and the
failures compound (malformed tool calls, forgotten discoveries, endless
edit-test loops, premature "it's fixed!").

## Hypothesis

Most of those responsibilities can be moved out of the model and into a
deterministic runtime. **Make the model do less, and make the system around it
smarter.** The model only ever answers one narrow question: *given this issue,
this repository, and this progress so far — what is the single next action?*
Everything else — stepping, verification, retries, budgets, safety — is owned
by the runtime.

## Architecture (current)

```
issue ──> AgentRuntime (state machine)
             │  builds bounded prompt: issue + repo map + compressed history
             ▼
          Small LLM (Ollama, JSON-constrained output)
             │  one structured action per step
             ▼
          parse + validate (Pydantic; 1 reformat retry on failure)
             │
     ┌───────┴────────┬──────────────┬─────────────┐
 read_file      search_code      edit_file     run_command
 (line ranges,  (ripgrep/py)     (unique       (allowlist, no shell,
  path feedback                   search/       timeout, truncation)
  on bad paths)                   replace,
                                  path feedback)
             │
   per step: loop detector (M2A) · stall-triggered verification (M2B)
             │
        model says "finish" — or the runtime verifies a stall
             ▼
   Deterministic verification: working tree changed? edited .py files
   compile? tests pass? — only then is the run a success.
```

The Milestone 1 core (structured single-action steps, deterministic
verification, repo sandbox, bounded stateless prompts, full JSONL
trajectories) is unchanged; three flag-gated reliability mechanisms sit on
top of it, each validated by its own ablation:

- **M2A — loop detection** (`--loop-detector`, default on). Fingerprints
  repeated identical actions (same action, arguments, working-tree diff hash,
  and result signature) and intervenes with a bounded strategy reset that
  preserves discoveries. Measured effect: it does **not** move solve rate
  (2/30 → 3/30 across 60 runs — within noise) but cuts prompt tokens ~11% and
  provides the stall signal M2B triggers on. Kept for those reasons, not for
  solve rate.
- **M2B — stall-triggered verification** (`--stall-verification`, default on).
  When the tree has changed but the model hasn't requested `finish`, the
  runtime periodically runs the same verification pipeline it would run at
  finish time and completes the run itself if everything passes. This
  converts "correct fix produced, never confirmed" — the dominant small-model
  failure — into solves.
- **M3 — path-resolution feedback** (`--path-feedback`, default on). When
  `read_file`/`edit_file` gets a non-existent path, the error includes a
  deterministic "Did you mean: `<path>`?" resolved from the real repository
  files (exact then case-insensitive basename match, suffix-disambiguated).
  The tool never redirects the operation; the model must retry explicitly.

## Measured results

All numbers come from ablation sweeps run by `evals/run_benchmark.py`
(2 models × 2 arms; 3 trials per task, or 5 in the preregistered
generalization study; fresh git baseline per trial; a success requires the
full deterministic verification pipeline to pass). Models
under test: `llama3.1:latest` (8B Q4_K_M) and `qwen2.5-coder:7b` (7.6B
Q4_K_M). Raw per-run rows are tracked under `results/benchmarks/`; full
reports live in `results/baseline/`.

| mechanism | study | solve rate | notes |
| --- | --- | --- | --- |
| M2A loop detection alone | 60 runs, 5 design tasks | 2/30 → 3/30 (noise) | prompt tokens −11%; kept as infrastructure |
| M2B stall verification | 60 runs, 5 design tasks | 0/30 → 20/30, p ≈ 1.4×10⁻⁸ | steps −47%, prompt tokens −49% |
| M2B — **held-out** | 96 runs, 8 unseen tasks | **5/48 → 29/48 (10% → 60%)**, p ≈ 4×10⁻⁷ | suite authored after the M2B freeze; no task regressed |
| M3 path feedback | 96 runs, same 8 tasks | llama 13/24 → 19/24 (p = 0.125); qwen 18/24 → 17/24 (variance) | llama GT-file read rate 15/24 → 24/24 (p = 0.0016) |
| M3 — **preregistered, independent suite** | 240 runs, 12 frozen tasks | llama 22/60 → 23/60; qwen 16/60 → 18/60 — **null in both** | llama GT-read 56/60 → 60/60 (+0.067 [+0.000, +0.200]); the solve-rate gain did not replicate |

The quoted p-values are two-sided Fisher exact tests that treat individual
runs as independent observations; trials are clustered within tasks, so these
tests are descriptive rather than strictly valid inference. The final row is
different: that study was preregistered, treats the **task** as the unit of
analysis, and reports task-cluster bootstrap intervals instead of a p-value
headline. Its full write-up is
[`results/analysis/m3-generalization-results.md`](results/analysis/m3-generalization-results.md).

Honest framing of each:

- **M2B is the load-bearing result.** Its held-out effect (10% → 60%) is the
  one measured on tasks the mechanism was never tuned against. Every success
  is a deterministic verification pass; in the design-set study all completions
  were runtime-attributed, and on the held-out suite the runtime's early
  verification sometimes *preempts* a finish the model would have reached — so
  the correct claim is that the runtime reaches a verified stop sooner and far
  more often, never that the models became better at judging completion.
- **M3 fixes a tool-interaction failure, and only that.** With path feedback
  on, every llama run that received a suggestion followed one and then read
  the file it needed — 11/11 in the first study, 9/9 in the independent one.
  What did *not* replicate is the payoff: the first study saw 8 of those 11
  runs go on to solve the task, the independent study saw **0 of 9**. On 12
  tasks authored without the mechanism in view, llama already read the right
  file in 93% of control runs, so the failure class M3 targets showed up in
  only 2 of 12 tasks (and 0 of 12 for qwen, which emitted zero suggestions in
  all 60 runs — the negative control replicating exactly). **M3 is kept, and
  its claim is re-scoped:** it removes a specific degenerate failure — one
  task burned 115 failed path lookups in the control arm — but it does not by
  itself produce solved tasks, and it costs ~17% wall-clock on llama.
- **Why the first M3 number was misleading, and how we knew to check.** The
  eight-task suite was genuinely held out for M2B, but M3 was *designed from*
  the analysis of M2B's failures on those same tasks — so for M3 it was an
  evaluation set, not evidence. That caveat was in this README before the
  follow-up ran; the preregistered 12-task study then confirmed it. This is
  what preregistration is for: the mechanism looked better than it was on the
  suite it was derived from, and only a frozen, independently authored suite
  could show that.

Reproduce the row-level tables from the tracked rows (stdlib only):

```bash
python -m evals.analyze_rows results/benchmarks/m3/rows.jsonl --expect-cell-size 24
```

(Ground-truth-file read rates and the M3 causal chain were derived from raw
trajectories, which are not committed; the reports say so where it applies.)

## Quickstart

```bash
git clone <this-repo> && cd smallcoder
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then edit: OLLAMA_BASE_URL, OLLAMA_MODEL
```

## Example

The repository ships a tiny buggy fixture project:

```bash
cp -r examples/demo-auth /tmp/demo-auth
cd /tmp/demo-auth && git init -q && git add -A && git commit -qm init && cd -

smallcoder solve \
  --repo /tmp/demo-auth \
  --issue "Login fails when the email address contains uppercase characters."
```

Inspect any run afterwards:

```bash
smallcoder inspect <run-id>
```

## Configuration

Everything is environment-driven (see [.env.example](.env.example)):

| Variable | Meaning | Default |
| --- | --- | --- |
| `SMALLCODER_PROVIDER` | Inference provider | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model tag (any <12B coding model) | *(required)* |
| `OLLAMA_FORMAT` | `json` / `schema` / `off` output constraint | `json` |
| `OLLAMA_FORCE_IPV4` | `1` forces IPv4 connections (`curl -4` equivalent) | off |
| `SMALLCODER_CONTEXT_LIMIT` | Context window in tokens (also `num_ctx`) | `12000` |
| `SMALLCODER_MAX_STEPS` | Hard step limit per run | `30` |
| `SMALLCODER_COMMAND_TIMEOUT` | Seconds per command | `120` |
| `SMALLCODER_ALLOWED_COMMANDS` | run_command allowlist | pytest, python, … |
| `SMALLCODER_RUNS_DIR` | Trajectory output dir | `results/runs` |
| `SMALLCODER_LOOP_DETECTOR` | M2A loop detection | on |
| `SMALLCODER_STALL_VERIFICATION` | M2B stall-triggered verification | on |
| `SMALLCODER_STALL_CHECK_INTERVAL` | Steps between stall checks | `5` |
| `SMALLCODER_PATH_FEEDBACK` | M3 path-resolution feedback | on |

Each mechanism also has a CLI ablation flag (`--loop-detector/--no-loop-detector`,
`--stall-verification/--no-stall-verification`, `--path-feedback/--no-path-feedback`).
No host, model, or credential is hard-coded. Never commit `.env`.

## Evaluation

- `evals/tasks/` + `evals/fixtures/` — the 5-task design suite (demo-auth,
  pagination, configload, storecart, csvparse) used to develop M2A/M2B.
- `evals/heldout/tasks/` + `evals/heldout/fixtures/` — 8 tasks authored after
  the M2B freeze (held out for M2B; reused as M3's evaluation/design set).
- `evals/m3_generalization/` — 12 tasks frozen and committed before any model
  run, for the preregistered independent M3 generalization study.
- `evals/run_m3_generalization.py` — resume-safe scheduler for that study: a
  fingerprinted 240-entry plan, deterministic run order, one retry on
  infrastructure error, and endpoint scrubbing on every persisted row.
- `evals/analyze_m3_generalization.py` — the preregistered analysis:
  trajectory-derived ground-truth-read extraction plus a task-cluster
  bootstrap, models never combined. Emits a sanitized per-run
  `mechanism.jsonl` so the primary outcome stays checkable without the
  uncommitted trajectories.
- `evals/run_benchmark.py` — ablation runner: one JSON row per run appended to
  `results/benchmarks/<study>/rows.jsonl`.
- `evals/analyze_rows.py` — stdlib-only analyzer that recomputes cell sizes,
  solve rates, per-task solves, metric means, and Fisher exact p-values from
  a tracked rows file, with duplicate-key detection and cell-size validation.
- `results/baseline/` — curated study reports; `results/analysis/` — the
  residual-failure analysis that motivated M3, plus the M3 generalization
  preregistration and its results.

## Development

```bash
pytest        # unit + e2e tests (mocked inference; no Ollama needed)
ruff check .
```

## Design decisions

- **Exact-unique search/replace edits** instead of unified diffs: small models
  malform diff hunks frequently; "old_text must match exactly once" gives
  deterministic application and produces actionable error messages the model
  can recover from.
- **Stateless per-step prompts** instead of an ever-growing chat transcript:
  the runtime re-renders issue + map + compressed history every step, which
  makes context budgeting a runtime concern rather than a model skill.
- **JSON mode by default, schema-constrained optional** (`OLLAMA_FORMAT=schema`):
  JSON mode works across Ollama versions; extraction still tolerates fences
  and prose as a last line of defense.
- **The runtime owns the loop.** Step limits, retry limits, finish limits, and
  verification are hard-coded control flow, not prompt suggestions.
- **Every mechanism ships behind an ablation flag** and is judged by an A/B
  sweep with tracked raw rows, not by anecdote. Mechanisms that fail to move
  the primary metric are documented as such (M2A).

## Limitations (current, honest)

- **Small studies.** All ablation cells are n = 15–24 runs on 5–8 small
  single-defect Python fixtures with two <12B models. Effects with p-values
  quoted above are real on these tasks; magnitudes are not precise estimates,
  and nothing here demonstrates generality to larger repositories or other
  languages.
- **M3's solve-rate effect is not statistically established** (p = 0.125),
  and its evaluation suite was not independently held out for M3 (see suite
  provenance above).
- **A rescue is only as trustworthy as the fixture's tests.** Runtime-verified
  completion inherits whatever the task's test suite fails to check.
- **Residual failures are mostly genuine reasoning failures** — wrong
  implementations produced after the model has read the correct file — which
  no runtime mechanism so far addresses.
- Context management is a naive char-budget truncation; token accounting uses
  a ~4 chars/token approximation for budgeting (real usage numbers come from
  Ollama's response counters).
- Verification auto-detection only knows pytest; other stacks need
  `--test-command`.
- Command allowlisting limits blast radius but is not a security sandbox;
  arbitrary Python executed via tests can still do arbitrary things. Run on
  repositories you trust, ideally in a container.

## Milestone history

1. **M1 — end-to-end baseline** (done): runtime, 4 tools, structured actions,
   deterministic verification, CLI, trajectories. Small-model baselines on the
   demo task: llama3.1 8B 0/10, qwen2.5-coder 7B 0/10 — motivating everything
   after.
2. **M2A — loop detection** (done): weak/negative on solve rate (2/30 → 3/30),
   ~11% prompt-token reduction; kept as infrastructure. Its failure analysis
   located the real bottleneck: models produce correct fixes but never
   request `finish`.
3. **M2B — stall-triggered verification** (done): 0/30 → 20/30 on the design
   suite; **5/48 → 29/48 (10% → 60%)** on 8 genuinely held-out tasks.
4. **M3 — path-resolution feedback** (done): designed from the held-out
   residual-failure analysis; llama GT-file read rate 15/24 → 24/24
   (p = 0.0016), solve rate 13/24 → 19/24 (promising, not established);
   inert for qwen.
5. **M3 generalization study** (done): 240 preregistered runs on 12
   independently frozen tasks. The mechanism replicated — 9/9 suggestions
   followed, llama GT-read 56/60 → 60/60 — but the solve-rate gain did not
   (22/60 → 23/60, interval spanning zero). Reported in full, including the
   retraction, in
   [`results/analysis/m3-generalization-results.md`](results/analysis/m3-generalization-results.md).
   It also independently replicated M2B: of 240 runs only 4 completions were
   model-initiated, and 75 of 79 successes were runtime-attributed.
6. **Next:** the missing control. Every comparison so far is SmallCoder
   against SmallCoder with a flag off — there is still no measurement against
   a *generic* agent loop (free-form tool calls, model-managed context, model
   decides when it is done) on the same model. That is the experiment the
   project's central claim actually rests on.
