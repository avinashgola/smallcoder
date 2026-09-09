# Benchmark rows summary: `results/benchmarks/m3/rows.jsonl`

96 rows · models: llama3.1:latest, qwen2.5-coder:7b · configs: loop-on+stall-on, loop-on+stall-on+path-on · 8 tasks

## Cells

| model | config | n | solved | rate | mean duration_s | mean file_not_found_errors | mean loop_detections | mean loop_interventions | mean model_calls | mean path_suggestions_emitted | mean path_suggestions_followed | mean stall_checks | mean steps | mean structured_output_failures | mean tokens_in | mean tokens_out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1:latest | loop-on+stall-on | 24 | 13 | 54% | 31.21 | 11.46 | 6.92 | 1.12 | 18.25 | 0.0 | 0.0 | 0.75 | 18.21 | 0.0 | 13636.71 | 844.12 |
| llama3.1:latest | loop-on+stall-on+path-on | 24 | 19 | 79% | 22.27 | 2.29 | 1.08 | 0.38 | 11.5 | 2.29 | 0.67 | 1.42 | 11.5 | 0.0 | 10828.5 | 658.54 |
| qwen2.5-coder:7b | loop-on+stall-on | 24 | 18 | 75% | 41.58 | 0.0 | 2.29 | 0.79 | 14.46 | 0.0 | 0.0 | 1.46 | 14.46 | 0.0 | 11225.33 | 1346.46 |
| qwen2.5-coder:7b | loop-on+stall-on+path-on | 24 | 17 | 71% | 43.07 | 0.0 | 1.71 | 0.71 | 14.75 | 0.0 | 0.0 | 1.79 | 14.75 | 0.0 | 11452.79 | 1456.88 |

## Completion modes

- llama3.1:latest / loop-on+stall-on: none: 11, runtime_rescued: 13
- llama3.1:latest / loop-on+stall-on+path-on: model_initiated: 1, none: 5, runtime_rescued: 18
- qwen2.5-coder:7b / loop-on+stall-on: model_initiated: 1, none: 6, runtime_rescued: 17
- qwen2.5-coder:7b / loop-on+stall-on+path-on: none: 7, runtime_rescued: 17

## Per-task solves

| task | llama3.1:latest / loop-on+stall-on | llama3.1:latest / loop-on+stall-on+path-on | qwen2.5-coder:7b / loop-on+stall-on | qwen2.5-coder:7b / loop-on+stall-on+path-on |
| --- | --- | --- | --- | --- |
| inventory | 3/3 | 3/3 | 1/3 | 2/3 |
| jsonflat | 1/3 | 1/3 | 3/3 | 2/3 |
| leapyear | 0/3 | 3/3 | 3/3 | 3/3 |
| logparse | 2/3 | 2/3 | 1/3 | 0/3 |
| ratelimit | 1/3 | 1/3 | 3/3 | 2/3 |
| tempconv | 0/3 | 3/3 | 3/3 | 3/3 |
| textstats | 3/3 | 3/3 | 2/3 | 2/3 |
| usergroups | 3/3 | 3/3 | 2/3 | 3/3 |

## Solve-rate comparison (Fisher exact, two-sided)

| model | loop-on+stall-on | loop-on+stall-on+path-on | p |
| --- | --- | --- | --- |
| llama3.1:latest | 13/24 | 19/24 | 0.125 |
| qwen2.5-coder:7b | 18/24 | 17/24 | 1.0 |
| combined | 31/48 | 36/48 | 0.374 |

*Derived from rows.jsonl only. Ground-truth-file read rates and suggestion causal chains require the gitignored trajectories and are not reproducible from this file.*
