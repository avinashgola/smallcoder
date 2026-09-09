# Benchmark rows summary: `results/benchmarks/generic_loop/rows_final.jsonl`

360 rows · models: llama3.1:latest, qwen2.5-coder:7b · configs: generic, generic+completion, smallcoder-A · 12 tasks

## Cells

| model | config | n | solved | rate | mean chars_sent_total | mean claimed_success | mean commands_run | mean delivered_success | mean duration_s | mean edits_failed | mean edits_ok | mean file_not_found_errors | mean loop_detections | mean loop_interventions | mean model_calls | mean model_latency_ms_total | mean n_messages_final | mean overclaim | mean path_suggestions_emitted | mean path_suggestions_followed | mean peak_context_chars | mean silent_success | mean stall_checks | mean steps | mean structured_output_failures | mean tampered | mean tokens_in | mean tokens_out | mean verified_checkpoint | mean verified_ever | mean verified_final |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1:latest | generic | 60 | 24 | 40% | 168610.52 | 0.72 | 3.27 | 0.4 | 32.86 | 5.22 | 3.15 | 0.53 | — | — | 16.95 | 31482.89 | 35.18 | 0.32 | — | — | 14219.7 | 0.0 | 0.0 | 16.8 | 0.12 | 0.03 | 47231.2 | 1001.97 | 0.1 | 0.4 | 0.4 |
| llama3.1:latest | generic+completion | 60 | 19 | 32% | 292303.22 | 0.58 | 4.03 | 0.25 | 49.62 | 7.42 | 4.18 | 0.47 | — | — | 22.18 | 46672.94 | 46.12 | 0.33 | — | — | 18446.17 | 0.08 | 2.22 | 22.12 | 0.02 | 0.03 | 82190.82 | 1560.78 | 0.08 | 0.33 | 0.33 |
| llama3.1:latest | smallcoder-A | 60 | 23 | 38% | — | 0.03 | 2.97 | 0.03 | 44.65 | — | — | 2.55 | 1.88 | 0.57 | 22.4 | — | — | 0.0 | 0.0 | 0.0 | — | 0.35 | 2.55 | 22.38 | 0.02 | 0.02 | 23658.0 | 1347.55 | 0.38 | — | 0.38 |
| qwen2.5-coder:7b | generic | 60 | 20 | 33% | 238679.73 | 0.37 | 2.95 | 0.33 | 61.15 | 1.48 | 2.97 | 0.0 | — | — | 22.37 | 59495.94 | 46.37 | 0.03 | — | — | 17090.67 | 0.0 | 0.0 | 22.37 | 0.0 | 0.02 | 65985.05 | 1952.67 | 0.23 | 0.33 | 0.33 |
| qwen2.5-coder:7b | generic+completion | 60 | 14 | 23% | 234515.8 | 0.05 | 1.43 | 0.05 | 60.41 | 2.9 | 1.53 | 0.0 | — | — | 24.1 | 58306.11 | 50.17 | 0.0 | — | — | 16029.2 | 0.2 | 0.88 | 24.07 | 0.05 | 0.03 | 64509.48 | 2081.73 | 0.22 | 0.25 | 0.25 |
| qwen2.5-coder:7b | smallcoder-A | 60 | 22 | 37% | — | 0.0 | 0.18 | 0.0 | 80.73 | — | — | 0.02 | 3.95 | 1.27 | 23.03 | — | — | 0.0 | 0.0 | 0.0 | — | 0.38 | 2.2 | 23.0 | 0.0 | 0.02 | 18066.45 | 2136.43 | 0.38 | — | 0.38 |

## Completion modes

- llama3.1:latest / generic: model_initiated: 43, none: 17
- llama3.1:latest / generic+completion: model_initiated: 15, none: 40, runtime_rescued: 5
- llama3.1:latest / smallcoder-A: model_initiated: 2, none: 37, runtime_rescued: 21
- qwen2.5-coder:7b / generic: model_initiated: 22, none: 38
- qwen2.5-coder:7b / generic+completion: model_initiated: 2, none: 45, runtime_rescued: 13
- qwen2.5-coder:7b / smallcoder-A: none: 37, runtime_rescued: 23

## Per-task solves

| task | llama3.1:latest / generic | llama3.1:latest / generic+completion | llama3.1:latest / smallcoder-A | qwen2.5-coder:7b / generic | qwen2.5-coder:7b / generic+completion | qwen2.5-coder:7b / smallcoder-A |
| --- | --- | --- | --- | --- | --- | --- |
| amounts | 1/5 | 0/5 | 1/5 | 0/5 | 1/5 | 2/5 |
| backoff | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 1/5 |
| booking | 1/5 | 0/5 | 2/5 | 0/5 | 0/5 | 1/5 |
| grading | 5/5 | 5/5 | 5/5 | 4/5 | 4/5 | 2/5 |
| invoices | 5/5 | 5/5 | 5/5 | 2/5 | 1/5 | 4/5 |
| leaderboard | 4/5 | 3/5 | 5/5 | 2/5 | 3/5 | 4/5 |
| ledger | 0/5 | 1/5 | 0/5 | 0/5 | 0/5 | 1/5 |
| notify | 3/5 | 1/5 | 0/5 | 2/5 | 2/5 | 2/5 |
| receipt | 1/5 | 1/5 | 1/5 | 3/5 | 0/5 | 1/5 |
| salesagg | 4/5 | 3/5 | 2/5 | 2/5 | 2/5 | 3/5 |
| semver | 0/5 | 0/5 | 0/5 | 3/5 | 1/5 | 1/5 |
| standings | 0/5 | 0/5 | 2/5 | 2/5 | 0/5 | 0/5 |

*Derived from rows.jsonl only. Ground-truth-file read rates and suggestion causal chains require the gitignored trajectories and are not reproducible from this file.*
