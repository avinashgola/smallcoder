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

## Architecture (Milestone 1)

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
 (line ranges)  (ripgrep/py)     (unique       (allowlist, no shell,
                                  search/       timeout, truncation)
                                  replace)
             │
        model says "finish"
             ▼
   Deterministic verification: working tree changed? edited .py files
   compile? tests pass? — only then is the run a success.
```

Key mechanics already in place:

- **Structured actions.** The model must emit one JSON object per step,
  validated against typed Pydantic schemas. One reformat retry with the exact
  parse error; repeated failures are counted (`structured_output_failures`)
  and abort the run after 3 consecutive misses.
- **Deterministic verification.** `finish` is a *request*, not a conclusion.
  The runtime checks that the working tree actually changed, edited Python
  files still compile, and the test command passes (explicit `--test-command`
  or auto-detected pytest). Failed verification is fed back to the model as an
  observation; after 3 rejected finishes the run fails.
- **Repo sandbox.** All paths resolve through a single chokepoint that rejects
  absolute paths, `..` traversal, symlink escapes, and `.git`. Commands run
  without a shell, from an executable allowlist, with timeouts and output
  truncation. SmallCoder never commits or pushes.
- **Bounded context.** Each step's prompt is rebuilt from scratch: issue +
  file listing + one-line summaries of old steps + the last few observations
  verbatim, trimmed oldest-first to a character budget derived from
  `SMALLCODER_CONTEXT_LIMIT` (~4 chars/token approximation, documented; a real
  context engine is Milestone 3).
- **Trajectories.** Every run writes `meta.json`, `trajectory.jsonl` (model
  calls, steps, parse errors, verification), full tool outputs, and
  `result.json` under `results/runs/<run-id>/`.

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
| `SMALLCODER_CONTEXT_LIMIT` | Context window in tokens (also `num_ctx`) | `12000` |
| `SMALLCODER_MAX_STEPS` | Hard step limit per run | `30` |
| `SMALLCODER_COMMAND_TIMEOUT` | Seconds per command | `120` |
| `SMALLCODER_ALLOWED_COMMANDS` | run_command allowlist | pytest, python, … |
| `SMALLCODER_RUNS_DIR` | Trajectory output dir | `results/runs` |

No host, model, or credential is hard-coded. Never commit `.env`.

## Development

```bash
pytest        # unit + e2e tests (mocked inference; no Ollama needed)
ruff check .
```

## Design decisions (Milestone 1)

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

## Limitations (current, honest)

- Context management is a naive char-budget truncation, not the planned
  keep/compress/drop engine (Milestone 3).
- No repository localization yet: the model sees a flat file listing and must
  search on its own (Milestone 2).
- No loop detection or failure-classification-driven recovery yet
  (Milestone 4). A model that thrashes will burn its step budget.
- Verification auto-detection only knows pytest; other stacks need
  `--test-command`.
- Token accounting uses a ~4 chars/token approximation for budgeting (real
  usage numbers come from Ollama's response counters).
- Command allowlisting limits blast radius but is not a security sandbox;
  arbitrary Python executed via tests can still do arbitrary things. Run on
  repositories you trust, ideally in a container.

## Roadmap

1. ~~**Milestone 1** — end-to-end baseline: runtime, tools, verification, CLI, trajectories~~ (this release)
2. **Milestone 2** — repository localization (repo map, deterministic candidate ranking)
3. **Milestone 3** — context engine (keep/compress/drop policy, budget accounting)
4. **Milestone 4** — reliability (failure taxonomy, loop detection, bounded recovery)
5. **Milestone 5** — evaluation harness (task fixtures, ablation flags, metrics)

No performance claims will appear here until the Milestone 5 harness produces
them.
