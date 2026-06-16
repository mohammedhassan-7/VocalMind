# VocalMind Ollama Cloud Benchmark - FULL_REPORT_v3

**Generated:** 2026-06-14 18:02 UTC
**Source directory:** `overnight_20260614`

## Run status

| Stage | Status | Observations | Expected | Repeats |
|---|---|---|---|---|
| emotion_shift | complete | 510 | 510 | 1 |
| process_adherence | complete | 765 | 765 | 1 |
| nli_policy | complete | 1032 | 1032 | 2 |
| rag_judge | complete | 300 | 300 | 1 |
| text_to_sql | complete | 150 | 150 | 1 |
| fast_classification | complete | 462 | 462 | 1 |
## Judge calibration

pending human scoring (0/49 filled)


## Per-stage quality (v2 pool)

### emotion_shift
| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |
|---|---|---|---|---|---|---|
| ministral-3:14b | 7.31 | 0.00 | 11377 | 30088 | 38318 | 170 |
| kimi-k2.5:cloud | 6.56 | 0.00 | 20844 | 36687 | 48280 | 170 |
| kimi-k2.6:cloud | 5.75 | 0.00 | 24826 | 50138 | 90313 | 170 |

### process_adherence
| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |
|---|---|---|---|---|---|---|
| qwen3.5:cloud | 6.65 | 0.00 | 56450 | 96678 | 112100 | 153 |
| kimi-k2.6:cloud | 5.51 | 0.00 | 40420 | 65114 | 109055 | 153 |
| kimi-k2.5:cloud | 5.34 | 0.00 | 48748 | 102000 | 127880 | 153 |
| ministral-3:8b | 4.36 | 0.00 | 18950 | 44881 | 52999 | 153 |
| ministral-3:14b | 4.15 | 0.00 | 21147 | 49852 | 66705 | 153 |

### nli_policy
| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |
|---|---|---|---|---|---|---|
| kimi-k2.5:cloud | 8.73 | 0.39 | 12884 | 45119 | 62095 | 344 |
| ministral-3:8b | 8.64 | 0.45 | 2786 | 4878 | 5879 | 344 |
| kimi-k2.6:cloud | 8.52 | 0.65 | 11638 | 61421 | 90524 | 344 |

### rag_judge
| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |
|---|---|---|---|---|---|---|
| ministral-3:8b | 9.36 | 0.00 | 2603 | 6661 | 10808 | 150 |
| kimi-k2.6:cloud | 8.18 | 0.00 | 13139 | 49069 | 59892 | 150 |

### text_to_sql

> **Note:** Scores from DB execution comparison (seeded BENCHMARK_ORG), not LLM judge.

| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |
|---|---|---|---|---|---|---|
| qwen3.5:cloud | 6.48 | 0.00 | 55920 | 495315 | 730044 | 50 |
| kimi-k2.6:cloud | 5.60 | 0.00 | 14604 | 28189 | 30670 | 50 |
| ministral-3:8b | 2.96 | 0.00 | 3821 | 9484 | 467616 | 50 |

### fast_classification
| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |
|---|---|---|---|---|---|---|
| ministral-3:14b | 8.44 | 0.00 | 1370 | 2589 | 5310 | 154 |
| ministral-3:8b | 8.28 | 0.00 | 1309 | 2270 | 3741 | 154 |
| kimi-k2.6:cloud | 8.18 | 0.00 | 3568 | 9159 | 13185 | 154 |

## Stability analysis (repeats >= 2)

- **nli_policy**: flagged high repeat variance: none

## Config recommendation

Review per-stage tables above. Default production stack unless larger-n results contradict:
- Heavy: `kimi-k2.6:cloud`
- Fast: `ministral-3:8b`
