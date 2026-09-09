# Benchmark rows summary: `results/benchmarks/m3_generalization/rows.jsonl`

240 rows · models: llama3.1:latest, qwen2.5-coder:7b · configs: loop-on+stall-on, loop-on+stall-on+path-on · 12 tasks

## Cells

| model | config | n | solved | rate | mean duration_s | mean file_not_found_errors | mean loop_detections | mean loop_interventions | mean model_calls | mean path_suggestions_emitted | mean path_suggestions_followed | mean stall_checks | mean steps | mean structured_output_failures | mean tokens_in | mean tokens_out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1:latest | loop-on+stall-on | 60 | 22 | 37% | 44.57 | 2.02 | 1.48 | 0.62 | 21.98 | 0.0 | 0.0 | 2.35 | 21.97 | 0.0 | 22573.32 | 1383.9 |
| llama3.1:latest | loop-on+stall-on+path-on | 60 | 23 | 38% | 52.32 | 1.05 | 0.72 | 0.63 | 23.28 | 1.05 | 0.33 | 2.87 | 23.27 | 0.0 | 24329.8 | 1464.5 |
| qwen2.5-coder:7b | loop-on+stall-on | 60 | 16 | 27% | 68.67 | 0.0 | 4.55 | 1.4 | 24.77 | 0.0 | 0.0 | 2.2 | 24.75 | 0.0 | 19702.65 | 2264.87 |
| qwen2.5-coder:7b | loop-on+stall-on+path-on | 60 | 18 | 30% | 63.3 | 0.0 | 5.52 | 1.55 | 24.5 | 0.0 | 0.0 | 1.8 | 24.48 | 0.0 | 18519.4 | 2245.42 |

## Completion modes

- llama3.1:latest / loop-on+stall-on: model_initiated: 2, none: 38, runtime_rescued: 20
- llama3.1:latest / loop-on+stall-on+path-on: model_initiated: 2, none: 37, runtime_rescued: 21
- qwen2.5-coder:7b / loop-on+stall-on: none: 44, runtime_rescued: 16
- qwen2.5-coder:7b / loop-on+stall-on+path-on: none: 42, runtime_rescued: 18

## Per-task solves

| task | llama3.1:latest / loop-on+stall-on | llama3.1:latest / loop-on+stall-on+path-on | qwen2.5-coder:7b / loop-on+stall-on | qwen2.5-coder:7b / loop-on+stall-on+path-on |
| --- | --- | --- | --- | --- |
| amounts | 0/5 | 2/5 | 1/5 | 3/5 |
| backoff | 0/5 | 0/5 | 0/5 | 0/5 |
| booking | 1/5 | 2/5 | 0/5 | 0/5 |
| grading | 5/5 | 4/5 | 2/5 | 3/5 |
| invoices | 5/5 | 5/5 | 3/5 | 2/5 |
| leaderboard | 5/5 | 4/5 | 5/5 | 5/5 |
| ledger | 1/5 | 1/5 | 0/5 | 1/5 |
| notify | 0/5 | 0/5 | 2/5 | 0/5 |
| receipt | 1/5 | 1/5 | 1/5 | 0/5 |
| salesagg | 4/5 | 4/5 | 1/5 | 1/5 |
| semver | 0/5 | 0/5 | 1/5 | 3/5 |
| standings | 0/5 | 0/5 | 0/5 | 0/5 |

## Solve-rate comparison (Fisher exact, two-sided)

| model | loop-on+stall-on | loop-on+stall-on+path-on | p |
| --- | --- | --- | --- |
| llama3.1:latest | 22/60 | 23/60 | 1.0 |
| qwen2.5-coder:7b | 16/60 | 18/60 | 0.84 |
| combined | 38/120 | 41/120 | 0.784 |

*Derived from rows.jsonl only. Ground-truth-file read rates and suggestion causal chains require the gitignored trajectories and are not reproducible from this file.*
