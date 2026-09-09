# M3 generalization analysis (preregistered)

240 runs · models analysed separately (no combined headline) · 12 tasks × 5 trials × 2 arms

## llama3.1:latest

| task | A gt-read | B gt-read | A solved | B solved | B−A gt-read | B−A solved |
| --- | --- | --- | --- | --- | --- | --- |
| amounts | 5/5 | 5/5 | 0/5 | 2/5 | +0.0 | +0.4 |
| backoff | 1/5 | 5/5 | 0/5 | 0/5 | +0.8 | +0.0 |
| booking | 5/5 | 5/5 | 1/5 | 2/5 | +0.0 | +0.2 |
| grading | 5/5 | 5/5 | 5/5 | 4/5 | +0.0 | -0.2 |
| invoices * | 5/5 | 5/5 | 5/5 | 5/5 | +0.0 | +0.0 |
| leaderboard | 5/5 | 5/5 | 5/5 | 4/5 | +0.0 | -0.2 |
| ledger | 5/5 | 5/5 | 1/5 | 1/5 | +0.0 | +0.0 |
| notify * | 5/5 | 5/5 | 0/5 | 0/5 | +0.0 | +0.0 |
| receipt | 5/5 | 5/5 | 1/5 | 1/5 | +0.0 | +0.0 |
| salesagg | 5/5 | 5/5 | 4/5 | 4/5 | +0.0 | +0.0 |
| semver | 5/5 | 5/5 | 0/5 | 0/5 | +0.0 | +0.0 |
| standings | 5/5 | 5/5 | 0/5 | 0/5 | +0.0 | +0.0 |

`*` ambiguous-candidate task (duplicate basenames).

- **gt_read**: arm A 56/60, arm B 60/60; task-cluster bootstrap B−A = +0.067 (95% CI [+0.000, +0.200], 10000 resamples, seed 20260815, unit=task); run-level Fisher p = 0.119 (descriptive only)
- **success**: arm A 22/60, arm B 23/60; task-cluster bootstrap B−A = +0.017 (95% CI [-0.067, +0.100], 10000 resamples, seed 20260815, unit=task); run-level Fisher p = 1.0 (descriptive only)

## qwen2.5-coder:7b

| task | A gt-read | B gt-read | A solved | B solved | B−A gt-read | B−A solved |
| --- | --- | --- | --- | --- | --- | --- |
| amounts | 5/5 | 4/5 | 1/5 | 3/5 | -0.2 | +0.4 |
| backoff | 5/5 | 5/5 | 0/5 | 0/5 | +0.0 | +0.0 |
| booking | 4/5 | 4/5 | 0/5 | 0/5 | +0.0 | +0.0 |
| grading | 2/5 | 4/5 | 2/5 | 3/5 | +0.4 | +0.2 |
| invoices * | 4/5 | 3/5 | 3/5 | 2/5 | -0.2 | -0.2 |
| leaderboard | 4/5 | 5/5 | 5/5 | 5/5 | +0.2 | +0.0 |
| ledger | 4/5 | 5/5 | 0/5 | 1/5 | +0.2 | +0.2 |
| notify * | 5/5 | 5/5 | 2/5 | 0/5 | +0.0 | -0.4 |
| receipt | 1/5 | 0/5 | 1/5 | 0/5 | -0.2 | -0.2 |
| salesagg | 5/5 | 5/5 | 1/5 | 1/5 | +0.0 | +0.0 |
| semver | 5/5 | 5/5 | 1/5 | 3/5 | +0.0 | +0.4 |
| standings | 0/5 | 0/5 | 0/5 | 0/5 | +0.0 | +0.0 |

`*` ambiguous-candidate task (duplicate basenames).

- **gt_read**: arm A 44/60, arm B 45/60; task-cluster bootstrap B−A = +0.017 (95% CI [-0.067, +0.117], 10000 resamples, seed 20260815, unit=task); run-level Fisher p = 1.0 (descriptive only)
- **success**: arm A 16/60, arm B 18/60; task-cluster bootstrap B−A = +0.033 (95% CI [-0.100, +0.167], 10000 resamples, seed 20260815, unit=task); run-level Fisher p = 0.84 (descriptive only)

