# Generic agent-loop control study (preregistered)

360 runs · models analysed separately (no pooled headline) · 12 tasks × 5 trials × 3 arms · unit of analysis: task

Primary endpoint `verified_final` (terminal state). `verified_checkpoint` is the anytime endpoint at **matched** checkpoints — reported for every arm, because SmallCoder stops at its first green checkpoint and terminal-only scoring would compare a maximum against a final value.

## llama3.1:latest

| arm | verified_final | verified_checkpoint | verified_ever |
| --- | --- | --- | --- |
| `smallcoder-A` | 23/60 | 23/60 | not measured |
| `generic` | 24/60 | 6/60 | 24/60 |
| `generic+completion` | 19/60 | 5/60 | 19/60 |

**smallcoder vs generic**

- `verified_final`: task-cluster bootstrap = -0.017 (95% CI [-0.167, +0.117], 10000 resamples, seed 20260908, unit=task); sign test p = 1.0 (3+/2−, floor 0.0625); Fisher p = 1.0 (descriptive only)
- `verified_checkpoint`: task-cluster bootstrap = +0.283 (95% CI [+0.100, +0.500], 10000 resamples, seed 20260908, unit=task); sign test p = 0.015625 (7+/0−, floor 0.015625); Fisher p = 0.000499 (descriptive only)
- `verified_ever`: **not measured for one arm — not compared**

**generic completion vs generic**

- `verified_final`: task-cluster bootstrap = -0.083 (95% CI [-0.167, +0.000], 10000 resamples, seed 20260908, unit=task); sign test p = 0.21875 (1+/5−, floor 0.03125); Fisher p = 0.446563 (descriptive only)
- `verified_checkpoint`: task-cluster bootstrap = -0.017 (95% CI [-0.083, +0.050], 10000 resamples, seed 20260908, unit=task); sign test p = 1.0 (2+/3−, floor 0.0625); Fisher p = 1.0 (descriptive only)
- `verified_ever`: task-cluster bootstrap = -0.083 (95% CI [-0.167, +0.000], 10000 resamples, seed 20260908, unit=task); sign test p = 0.21875 (1+/5−, floor 0.03125); Fisher p = 0.446563 (descriptive only)

**smallcoder vs generic completion**

- `verified_final`: task-cluster bootstrap = +0.067 (95% CI [-0.050, +0.200], 10000 resamples, seed 20260908, unit=task); sign test p = 1.0 (4+/3−, floor 0.015625); Fisher p = 0.56613 (descriptive only)
- `verified_checkpoint`: task-cluster bootstrap = +0.300 (95% CI [+0.100, +0.533], 10000 resamples, seed 20260908, unit=task); sign test p = 0.070312 (7+/1−, floor 0.007812); Fisher p = 0.000167 (descriptive only)
- `verified_ever`: **not measured for one arm — not compared**

| task | smallcoder-A final | generic final | generic+completion final | smallcoder-A ckpt | generic ckpt | generic+completion ckpt |
| --- | --- | --- | --- | --- | --- | --- |
| amounts | 1/5 | 1/5 | 0/5 | 1/5 | 0/5 | 0/5 |
| backoff | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| booking | 2/5 | 1/5 | 0/5 | 2/5 | 1/5 | 0/5 |
| grading | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 | 0/5 |
| invoices | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 | 0/5 |
| leaderboard | 5/5 | 4/5 | 3/5 | 5/5 | 3/5 | 2/5 |
| ledger | 0/5 | 0/5 | 1/5 | 0/5 | 0/5 | 0/5 |
| notify | 0/5 | 3/5 | 1/5 | 0/5 | 0/5 | 1/5 |
| receipt | 1/5 | 1/5 | 1/5 | 1/5 | 0/5 | 1/5 |
| salesagg | 2/5 | 4/5 | 3/5 | 2/5 | 2/5 | 1/5 |
| semver | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| standings | 2/5 | 0/5 | 0/5 | 2/5 | 0/5 | 0/5 |

Exploratory counts (per arm, 60 runs each):

| arm | claimed_success | overclaim | silent_success | delivered_success | tampered | context_overflow |
| --- | --- | --- | --- | --- | --- | --- |
| `smallcoder-A` | 2 | 0 | 21 | 2 | 1 | 0 |
| `generic` | 43 | 19 | 0 | 24 | 2 | 0 |
| `generic+completion` | 35 | 20 | 5 | 15 | 2 | 0 |

Preregistered verdict — (a) thesis falsified: **False**; (b) thesis narrows: **False**; (c) inconclusive: **True**

Cost (per run). `tokens_in` and `duration_s` are **not comparable across arms** — KV-cache deflation favours the accumulating transcript, and SmallCoder's early stop and per-step git/pytest work favour it in the other direction — so they are shown, never differenced.

| arm | steps | model_calls | tokens_out | chars_sent_total | peak_context_chars | tokens_in* | duration_s* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `smallcoder-A` | 22.38 | 22.4 | 1347.55 | None | None | 23658.0 | 44.65 |
| `generic` | 16.8 | 16.95 | 1001.97 | 168610.52 | 14219.7 | 47231.2 | 32.86 |
| `generic+completion` | 22.12 | 22.18 | 1560.78 | 292303.22 | 18446.17 | 82190.82 | 49.62 |

## qwen2.5-coder:7b

| arm | verified_final | verified_checkpoint | verified_ever |
| --- | --- | --- | --- |
| `smallcoder-A` | 22/60 | 22/60 | not measured |
| `generic` | 20/60 | 14/60 | 20/60 |
| `generic+completion` | 14/60 | 12/60 | 14/60 |

**smallcoder vs generic**

- `verified_final`: task-cluster bootstrap = +0.033 (95% CI [-0.150, +0.217], 10000 resamples, seed 20260908, unit=task); sign test p = 0.548828 (7+/4−, floor 0.000977); Fisher p = 0.848369 (descriptive only)
- `verified_checkpoint`: task-cluster bootstrap = +0.133 (95% CI [-0.050, +0.300], 10000 resamples, seed 20260908, unit=task); sign test p = 0.226562 (8+/3−, floor 0.000977); Fisher p = 0.162728 (descriptive only)
- `verified_ever`: **not measured for one arm — not compared**

**generic completion vs generic**

- `verified_final`: task-cluster bootstrap = -0.100 (95% CI [-0.233, +0.033], 10000 resamples, seed 20260908, unit=task); sign test p = 0.6875 (2+/4−, floor 0.03125); Fisher p = 0.311128 (descriptive only)
- `verified_checkpoint`: task-cluster bootstrap = -0.033 (95% CI [-0.183, +0.117], 10000 resamples, seed 20260908, unit=task); sign test p = 1.0 (4+/4−, floor 0.007812); Fisher p = 0.824993 (descriptive only)
- `verified_ever`: task-cluster bootstrap = -0.100 (95% CI [-0.233, +0.033], 10000 resamples, seed 20260908, unit=task); sign test p = 0.6875 (2+/4−, floor 0.03125); Fisher p = 0.311128 (descriptive only)

**smallcoder vs generic completion**

- `verified_final`: task-cluster bootstrap = +0.133 (95% CI [+0.000, +0.250], 10000 resamples, seed 20260908, unit=task); sign test p = 0.039062 (8+/1−, floor 0.003906); Fisher p = 0.162728 (descriptive only)
- `verified_checkpoint`: task-cluster bootstrap = +0.167 (95% CI [+0.050, +0.283], 10000 resamples, seed 20260908, unit=task); sign test p = 0.039062 (8+/1−, floor 0.003906); Fisher p = 0.067416 (descriptive only)
- `verified_ever`: **not measured for one arm — not compared**

| task | smallcoder-A final | generic final | generic+completion final | smallcoder-A ckpt | generic ckpt | generic+completion ckpt |
| --- | --- | --- | --- | --- | --- | --- |
| amounts | 2/5 | 0/5 | 1/5 | 2/5 | 0/5 | 1/5 |
| backoff | 1/5 | 0/5 | 0/5 | 1/5 | 0/5 | 0/5 |
| booking | 1/5 | 0/5 | 0/5 | 1/5 | 0/5 | 0/5 |
| grading | 2/5 | 4/5 | 4/5 | 2/5 | 2/5 | 3/5 |
| invoices | 4/5 | 2/5 | 1/5 | 4/5 | 2/5 | 1/5 |
| leaderboard | 4/5 | 2/5 | 3/5 | 4/5 | 1/5 | 3/5 |
| ledger | 1/5 | 0/5 | 0/5 | 1/5 | 0/5 | 0/5 |
| notify | 2/5 | 2/5 | 2/5 | 2/5 | 1/5 | 2/5 |
| receipt | 1/5 | 3/5 | 0/5 | 1/5 | 3/5 | 0/5 |
| salesagg | 3/5 | 2/5 | 2/5 | 3/5 | 1/5 | 1/5 |
| semver | 1/5 | 3/5 | 1/5 | 1/5 | 3/5 | 1/5 |
| standings | 0/5 | 2/5 | 0/5 | 0/5 | 1/5 | 0/5 |

Exploratory counts (per arm, 60 runs each):

| arm | claimed_success | overclaim | silent_success | delivered_success | tampered | context_overflow |
| --- | --- | --- | --- | --- | --- | --- |
| `smallcoder-A` | 0 | 0 | 23 | 0 | 1 | 0 |
| `generic` | 22 | 2 | 0 | 20 | 1 | 1 |
| `generic+completion` | 3 | 0 | 12 | 3 | 2 | 1 |

Preregistered verdict — (a) thesis falsified: **False**; (b) thesis narrows: **True**; (c) inconclusive: **True**

Cost (per run). `tokens_in` and `duration_s` are **not comparable across arms** — KV-cache deflation favours the accumulating transcript, and SmallCoder's early stop and per-step git/pytest work favour it in the other direction — so they are shown, never differenced.

| arm | steps | model_calls | tokens_out | chars_sent_total | peak_context_chars | tokens_in* | duration_s* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `smallcoder-A` | 23.0 | 23.03 | 2136.43 | None | None | 18066.45 | 80.73 |
| `generic` | 22.37 | 22.37 | 1952.67 | 238679.73 | 17090.67 | 65985.05 | 61.15 |
| `generic+completion` | 24.07 | 24.1 | 2081.73 | 234515.8 | 16029.2 | 64509.48 | 60.41 |

## Drift check — fresh treatment vs frozen M3 arm A

- llama3.1:latest: fresh 23/60 vs frozen 22/60
- qwen2.5-coder:7b: fresh 22/60 vs frozen 16/60

If the fresh rate falls inside the frozen study's per-model interval, frozen-row comparisons are licensed and this is also a reproducibility result; otherwise every frozen-row comparison is dropped.

