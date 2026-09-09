# Benchmark rows summary: `results/benchmarks/heldout/rows.jsonl`

96 rows · models: llama3.1:latest, qwen2.5-coder:7b · configs: detector-on, loop-on+stall-on · 8 tasks

**Duplicate keys resolved by dedupe policy:**
- `llama3.1:latest/loop-on+stall-on/inventory/1` on lines 25, 74

## Cells

| model | config | n | solved | rate | mean duration_s | mean loop_detections | mean loop_interventions | mean model_calls | mean stall_checks | mean steps | mean structured_output_failures | mean tokens_in | mean tokens_out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1:latest | detector-on | 24 | 1 | 4% | 54.52 | 5.83 | 1.21 | 29.5 | 0.0 | 29.5 | 0.0 | 27535.25 | 1685.25 |
| llama3.1:latest | loop-on+stall-on | 24 | 11 | 46% | 32.92 | 6.92 | 1.04 | 19.17 | 0.88 | 19.17 | 0.0 | 15418.88 | 923.75 |
| qwen2.5-coder:7b | detector-on | 24 | 4 | 17% | 82.51 | 3.08 | 1.12 | 26.79 | 0.0 | 26.75 | 0.0 | 23493.33 | 2817.62 |
| qwen2.5-coder:7b | loop-on+stall-on | 24 | 18 | 75% | 37.51 | 1.71 | 0.71 | 12.96 | 1.71 | 12.96 | 0.0 | 10155.58 | 1244.0 |

## Completion modes

- llama3.1:latest / detector-on: model_initiated: 1, none: 23
- llama3.1:latest / loop-on+stall-on: none: 13, runtime_rescued: 11
- qwen2.5-coder:7b / detector-on: model_initiated: 4, none: 20
- qwen2.5-coder:7b / loop-on+stall-on: none: 6, runtime_rescued: 18

## Per-task solves

| task | llama3.1:latest / detector-on | llama3.1:latest / loop-on+stall-on | qwen2.5-coder:7b / detector-on | qwen2.5-coder:7b / loop-on+stall-on |
| --- | --- | --- | --- | --- |
| inventory | 1/3 | 3/3 | 0/3 | 1/3 |
| jsonflat | 0/3 | 0/3 | 0/3 | 2/3 |
| leapyear | 0/3 | 0/3 | 0/3 | 3/3 |
| logparse | 0/3 | 2/3 | 0/3 | 2/3 |
| ratelimit | 0/3 | 0/3 | 3/3 | 3/3 |
| tempconv | 0/3 | 0/3 | 1/3 | 3/3 |
| textstats | 0/3 | 3/3 | 0/3 | 1/3 |
| usergroups | 0/3 | 3/3 | 0/3 | 3/3 |

## Solve-rate comparison (Fisher exact, two-sided)

| model | detector-on | loop-on+stall-on | p |
| --- | --- | --- | --- |
| llama3.1:latest | 1/24 | 11/24 | 0.0018 |
| qwen2.5-coder:7b | 4/24 | 18/24 | 0.000111 |
| combined | 5/48 | 29/48 | 3.98e-07 |

*Derived from rows.jsonl only. Ground-truth-file read rates and suggestion causal chains require the gitignored trajectories and are not reproducible from this file.*
