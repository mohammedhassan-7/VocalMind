# Leaderboard validation v7 (recomputed from checkpoints)

**Generated:** 2026-06-15 13:47 UTC  
**Ground truth:** `ollama_cloud_ground_truth_v2.json`  
**Dedup:** one row per `(model, sample_id)`, last checkpoint line wins.

## Summary vs FULL_REPORT_v7 claims

| Stage | Claimed winner | Claimed | Recomputed winner | Recomputed | Match? |
|---|---|---:|---|---:|---|
| emotion_shift | `kimi-k2.5:cloud` | 0.530 | `kimi-k2.5:cloud` | 0.529 | YES |

### emotion_shift — per model

| Model | n | exact % | parseable % |
|---|---:|---:|---:|
| kimi-k2.5:cloud | 170 | 52.9% | 100.0% |
| ministral-3:14b | 170 | 47.6% | 100.0% |
| kimi-k2.6:cloud | 170 | 47.6% | 100.0% |

| process_adherence | `kimi-k2.6:cloud` | 0.546 | `kimi-k2.6:cloud` | 0.546 | YES |

### process_adherence — per model

| Model | n | exact % | F1 incl | F1 excl | extract_err |
|---|---:|---:|---:|---:|---:|
| kimi-k2.6:cloud | 153 | 43.1% | 0.546 | 0.572 | 7 |
| qwen3.5:cloud | 153 | 35.3% | 0.430 | 0.621 | 47 |
| kimi-k2.5:cloud | 153 | 30.1% | 0.404 | 0.494 | 28 |
| ministral-3:8b | 153 | 11.8% | 0.123 | 0.293 | 89 |
| ministral-3:14b | 153 | 11.8% | 0.122 | 0.291 | 89 |

| nli_policy | `ministral-3:8b` | 0.520 | `ministral-3:8b` | 0.517 | YES |

### nli_policy — per model

| Model | n | exact % | parseable % |
|---|---:|---:|---:|
| ministral-3:8b | 172 | 51.7% | 100.0% |
| kimi-k2.5:cloud | 172 | 49.4% | 100.0% |
| kimi-k2.6:cloud | 172 | 49.4% | 100.0% |

| rag_judge | `ministral-3:8b` | 0.950 | `ministral-3:8b` | 0.953 | YES |

### rag_judge — per model

| Model | n | exact % | parseable % |
|---|---:|---:|---:|
| ministral-3:8b | 150 | 95.3% | 99.3% |
| kimi-k2.6:cloud | 150 | 81.3% | 99.3% |

| text_to_sql | `qwen3.5:cloud` | 0.540 | `qwen3.5:cloud` | 0.540 | YES |

### text_to_sql — per model

| Model | n | exact % | parseable % |
|---|---:|---:|---:|
| qwen3.5:cloud | 50 | 54.0% | 100.0% |
| kimi-k2.6:cloud | 50 | 38.0% | 100.0% |
| ministral-3:8b | 50 | 20.0% | 100.0% |

| fast_classification | `ministral-3:14b` | 0.690 | `ministral-3:14b` | 0.695 | YES |

### fast_classification — per model

| Model | n | exact % | parseable % |
|---|---:|---:|---:|
| ministral-3:14b | 154 | 69.5% | 100.0% |
| kimi-k2.6:cloud | 154 | 68.2% | 100.0% |
| ministral-3:8b | 154 | 67.5% | 100.0% |

## Data sources

- **emotion_shift:** `emotion_shift_v2.checkpoint.jsonl`
- **process_adherence:** `process_adherence.checkpoint.jsonl`
- **nli_policy:** `nli_policy.checkpoint.jsonl`
- **rag_judge:** `rag_judge.checkpoint.jsonl`
- **text_to_sql:** `text_to_sql.checkpoint.jsonl`
- **fast_classification:** `fast_classification.checkpoint.jsonl`

Re-run: `python infra/scripts/validate_leaderboard_v7.py`  (no API calls; scores saved `raw_response` from overnight run).