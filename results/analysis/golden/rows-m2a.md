# Benchmark rows summary: `results/benchmarks/m2a/rows.jsonl`

60 rows · models: llama3.1:latest, qwen2.5-coder:7b · configs: detector-off, detector-on · 5 tasks

## Cells

| model | config | n | solved | rate | mean duration_s | mean loop_detections | mean loop_interventions | mean model_calls | mean steps | mean structured_output_failures | mean tokens_in | mean tokens_out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1:latest | detector-off | 15 | 1 | 7% | 80.6 | 0.0 | 0.0 | 29.73 | 29.73 | 0.0 | 31934.2 | 2027.4 |
| llama3.1:latest | detector-on | 15 | 1 | 7% | 78.03 | 0.6 | 0.6 | 29.0 | 29.0 | 0.0 | 30094.8 | 1848.67 |
| qwen2.5-coder:7b | detector-off | 15 | 1 | 7% | 147.85 | 0.0 | 0.0 | 29.8 | 29.4 | 0.0 | 28001.73 | 3045.87 |
| qwen2.5-coder:7b | detector-on | 15 | 2 | 13% | 101.62 | 1.8 | 1.0 | 28.6 | 28.6 | 0.0 | 23475.93 | 2899.53 |

## Completion modes

- llama3.1:latest / detector-off: unrecorded: 15
- llama3.1:latest / detector-on: unrecorded: 15
- qwen2.5-coder:7b / detector-off: unrecorded: 15
- qwen2.5-coder:7b / detector-on: unrecorded: 15

## Per-task solves

| task | llama3.1:latest / detector-off | llama3.1:latest / detector-on | qwen2.5-coder:7b / detector-off | qwen2.5-coder:7b / detector-on |
| --- | --- | --- | --- | --- |
| configload | 0/3 | 0/3 | 0/3 | 0/3 |
| csvparse | 0/3 | 1/3 | 0/3 | 1/3 |
| demo-auth | 0/3 | 0/3 | 0/3 | 0/3 |
| pagination | 0/3 | 0/3 | 1/3 | 1/3 |
| storecart | 1/3 | 0/3 | 0/3 | 0/3 |

## Solve-rate comparison (Fisher exact, two-sided)

| model | detector-off | detector-on | p |
| --- | --- | --- | --- |
| llama3.1:latest | 1/15 | 1/15 | 1.0 |
| qwen2.5-coder:7b | 1/15 | 2/15 | 1.0 |
| combined | 2/30 | 3/30 | 1.0 |

*Derived from rows.jsonl only. Ground-truth-file read rates and suggestion causal chains require the gitignored trajectories and are not reproducible from this file.*
