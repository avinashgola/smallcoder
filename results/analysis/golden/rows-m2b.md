# Benchmark rows summary: `results/benchmarks/m2b/rows.jsonl`

60 rows · models: llama3.1:latest, qwen2.5-coder:7b · configs: detector-on, loop-on+stall-on · 5 tasks

## Cells

| model | config | n | solved | rate | mean duration_s | mean loop_detections | mean loop_interventions | mean model_calls | mean stall_checks | mean steps | mean structured_output_failures | mean tokens_in | mean tokens_out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1:latest | detector-on | 15 | 0 | 0% | 78.57 | 0.8 | 0.8 | 30.0 | 0.0 | 30.0 | 0.0 | 30210.2 | 1883.73 |
| llama3.1:latest | loop-on+stall-on | 15 | 8 | 53% | 58.7 | 0.47 | 0.47 | 19.0 | 2.53 | 18.93 | 0.0 | 18440.13 | 1221.33 |
| qwen2.5-coder:7b | detector-on | 15 | 0 | 0% | 127.6 | 0.8 | 0.8 | 30.0 | 0.0 | 30.0 | 0.0 | 25651.0 | 3088.13 |
| qwen2.5-coder:7b | loop-on+stall-on | 15 | 12 | 80% | 138.12 | 0.27 | 0.27 | 12.53 | 1.87 | 12.6 | 0.0 | 9966.93 | 1305.07 |

## Completion modes

- llama3.1:latest / detector-on: none: 15
- llama3.1:latest / loop-on+stall-on: none: 7, runtime_rescued: 8
- qwen2.5-coder:7b / detector-on: none: 15
- qwen2.5-coder:7b / loop-on+stall-on: none: 3, runtime_rescued: 12

## Per-task solves

| task | llama3.1:latest / detector-on | llama3.1:latest / loop-on+stall-on | qwen2.5-coder:7b / detector-on | qwen2.5-coder:7b / loop-on+stall-on |
| --- | --- | --- | --- | --- |
| configload | 0/3 | 0/3 | 0/3 | 2/3 |
| csvparse | 0/3 | 1/3 | 0/3 | 1/3 |
| demo-auth | 0/3 | 1/3 | 0/3 | 3/3 |
| pagination | 0/3 | 3/3 | 0/3 | 3/3 |
| storecart | 0/3 | 3/3 | 0/3 | 3/3 |

## Solve-rate comparison (Fisher exact, two-sided)

| model | detector-on | loop-on+stall-on | p |
| --- | --- | --- | --- |
| llama3.1:latest | 0/15 | 8/15 | 0.0022 |
| qwen2.5-coder:7b | 0/15 | 12/15 | 1.05e-05 |
| combined | 0/30 | 20/30 | 1.43e-08 |

*Derived from rows.jsonl only. Ground-truth-file read rates and suggestion causal chains require the gitignored trajectories and are not reproducible from this file.*
