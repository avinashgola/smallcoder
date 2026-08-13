# Baseline: gemma4:31b on demo-auth (Milestone 1 integration validation)

**Date:** 2026-08-13
**Purpose:** Validate the Milestone 1 runtime end-to-end against a real remote
Ollama backend. This is an *integration baseline*, not a benchmark: 4 runs on a
single trivial task carry no statistical significance.

## Setup

| Item | Value |
| --- | --- |
| SmallCoder version | 0.1.0 |
| Git commit | adb22dc (+ uncommitted IPv4-transport fix, see below) |
| Python | 3.12.10 |
| Model | `gemma4:31b` (remote Ollama 0.21.0; private host, not recorded) |
| Task | examples/demo-auth: "Login fails when the email address contains uppercase characters." |
| Structured output | `OLLAMA_FORMAT=json` (Ollama JSON mode) |
| Context limit | 12000 tokens (`num_ctx`), ~33.6k char prompt budget |
| Max steps | 30 |
| Test command | auto-detected: `python -m pytest -q --no-header -p no:cacheprovider` |
| Networking | `OLLAMA_FORCE_IPV4=1` (NAT64/DNS64 network; see integration fix) |

Note: `gemma4:31b` is the **large reference model**, not the <12B research
target. This baseline validates the runtime plumbing; the <12B experiments are
Milestone 2+ work.

## Results

4/4 successful runs (excluding one pre-fix run that failed with
`OLLAMA_CONNECTION` before any model call; see "Integration fix").

| run_id | success | steps | tool calls | model calls | reformat retries | struct. failures | verif. rejections | tokens in | tokens out | avg call latency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20260813-140651-b041 | yes | 8 | 7 | 9 | 1 | 0 | 0 | 9164 | 1005 | 6.9 s |
| 20260813-140817-08c6 | yes | 9 | 8 | 9 | 0 | 0 | 0 | 9395 | 909 | 5.8 s |
| 20260813-140911-c7cb | yes | 9 | 8 | 9 | 0 | 0 | 0 | 8925 | 1076 | 7.5 s |
| 20260813-141020-f9c8 | yes | 9 | 8 | 9 | 0 | 0 | 0 | 9600 | 986 | 6.4 s |

**Aggregates:** solve rate 4/4 (100%). Mean steps 8.75, mean tool calls 7.75,
mean model calls 9.0, mean tokens in 9271, mean tokens out 994, mean per-call
latency ~6.6 s (~60 s model time per run).

**Fix quality:** all 4 runs produced the identical, correct, minimal 1-line
change (`stored = USERS.get(email.strip())` → `...strip().lower()`), edited
only `app.py`, and passed deterministic verification (changes_present,
python_syntax, pytest 3/3) on the first `finish`. No premature finish attempts.
No files outside the target repository were touched.

## Representative action sequence (run 20260813-140651-b041)

```text
1. read_file app.py                              ok
2. run_command pytest tests/test_auth.py         failed (import error, see below)
3. run_command PYTHONPATH=. pytest ...           failed (env prefix rejected by allowlist)
4. run_command python3 -m pytest tests/...       failed (real failing test surfaced)
5. read_file app.py                              ok
6. edit_file app.py                              ok   (one reformat retry: model
                                                       omitted "path"; recovered)
7. run_command python3 -m pytest tests/...       ok
8. finish -> deterministic verification          PASSED
```

This matches the intended loop: read → reproduce → understand → edit → test →
finish → verify.

## Observed behavior (kept as baseline data, not patched)

1. **Bare `pytest` import friction (all 4 runs, 2–4 wasted steps).** The demo
   fixture has no root `conftest.py`, so bare `pytest` cannot `import app`;
   only `python -m pytest` (cwd on `sys.path`) works. Every run burned steps
   discovering this, one run re-trying bare `pytest` twice (an early
   repeated-action signature — motivating Milestone 4's loop detector).
   Verification always used `python -m pytest`, so it was unaffected.
2. **Shell-isms rejected cleanly.** Models tried `PYTHONPATH=. pytest` (2 runs)
   and `ls -R` (1 run); the allowlist rejected both with actionable errors and
   the model recovered every time.
3. **Structured output is solid in JSON mode.** 37 model calls total produced
   exactly 1 malformed action (missing `path` argument); the single reformat
   retry with the validation error message recovered it. Zero
   structured-output failures recorded.
4. **Token growth is bounded.** Prompt sizes stayed ~1.7k–4.5k chars
   (~420–1240 tokens in), well under budget — expected on a toy repo; the
   context engine (Milestone 3) is what this metric will stress later.

## Integration fix made during validation (category B)

The first attempt failed with `OLLAMA_CONNECTION` before any model call: the
local network is NAT64/DNS64, and macOS `getaddrinfo` synthesizes unreachable
IPv6 addresses (64:ff9b::/96) **even for IPv4-literal URLs**. The original
`OLLAMA_FORCE_IPV4` implementation (bind local address `0.0.0.0`) failed there
with `EAFNOSUPPORT`, because the resolver returned no IPv4 candidate at all.
Fixed by resolving with `AF_INET` in a custom httpcore network backend
(`ForceIPv4Transport` in `smallcoder/models/ollama.py`). No agent-runtime
changes were needed.

## Verdict

Milestone 1 is validated end-to-end against a real backend and ready to
freeze. Next: repeat this protocol with a <12B model (the actual research
target) before starting Milestone 2, so localization has a true small-model
baseline to improve on.
