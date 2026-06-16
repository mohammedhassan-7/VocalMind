# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v5

**Generated:** 2026-06-15 15:30 UTC
**Primary metric:** ground-truth exact match (objective comparison, no LLM judge)
**Source:** Re-scored from saved raw responses in `overnight_20260614/` (zero new API calls)

## Run status (unchanged from v3)

| Stage | Observations | Errors |
|---|---:|---:|
| emotion_shift | 510 | 0 |
| process_adherence | 765 | 0 |
| nli_policy | 1032 | 0 |
| rag_judge | 300 | 0 |
| text_to_sql | 150 | 0 |
| fast_classification | 462 | 0 |

## Per-stage results (ground-truth scoring)

### emotion_shift
> Exact/partial match against reference label or structured answer.

| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:14b | 15% | 1.47 | 26% | 11377 | 30088 | 170 |
| kimi-k2.5:cloud | 13% | 1.29 | 52% | 20844 | 36687 | 170 |
| kimi-k2.6:cloud | 7% | 0.71 | 82% | 24826 | 50138 | 170 |

### process_adherence
> F1-based set match on missing SOP steps (precision/recall).

| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| kimi-k2.6:cloud | 43% | 5.46 | 5% | 40420 | 65114 | 153 |
| qwen3.5:cloud | 35% | 4.30 | 31% | 56450 | 96678 | 153 |
| kimi-k2.5:cloud | 30% | 4.04 | 18% | 48748 | 102000 | 153 |
| ministral-3:14b | 12% | 1.22 | 58% | 21147 | 49852 | 153 |
| ministral-3:8b | 12% | 1.23 | 58% | 18950 | 44881 | 153 |

- **kimi-k2.6:cloud** mean F1: 0.546
- **qwen3.5:cloud** mean F1: 0.430
- **kimi-k2.5:cloud** mean F1: 0.404
- **ministral-3:8b** mean F1: 0.123
- **ministral-3:14b** mean F1: 0.122

### nli_policy
> Exact/partial match against reference label or structured answer.

| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:8b | 70% | 6.98 | 0% | 2765 | 4841 | 172 |
| kimi-k2.5:cloud | 60% | 6.05 | 0% | 13506 | 49394 | 172 |
| kimi-k2.6:cloud | 59% | 5.93 | 0% | 11894 | 56692 | 172 |

### rag_judge
> Exact/partial match against reference label or structured answer.

| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:8b | 95% | 9.73 | 1% | 2603 | 6661 | 150 |
| kimi-k2.6:cloud | 81% | 9.03 | 1% | 13139 | 49069 | 150 |

### text_to_sql
> Execution-based scoring (unchanged from v3).

| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.5:cloud | 54% | 6.48 | 0% | 55920 | 495315 | 50 |
| kimi-k2.6:cloud | 38% | 5.60 | 0% | 14604 | 28189 | 50 |
| ministral-3:8b | 20% | 2.96 | 0% | 3821 | 9484 | 50 |

### fast_classification
> Exact/partial match against reference label or structured answer.

| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:14b | 69% | 8.25 | 0% | 1370 | 2589 | 154 |
| kimi-k2.6:cloud | 68% | 8.12 | 0% | 3568 | 9159 | 154 |
| ministral-3:8b | 68% | 8.05 | 0% | 1309 | 2270 | 154 |

## Recommendation table (exact-match driven)

| Role | Model | Exact match | Notes |
|---|---|---:|---|
| Heavy (emotion_shift) | `ministral-3:14b` | exact=15%, parseable=74%, exact|parseable=20% | Primary metric |
| Heavy (nli_policy) | `ministral-3:8b` | 70% | Primary metric |
| Heavy (process_adherence) | `kimi-k2.6:cloud` | F1=0.55, exact=43% | Primary metric |
| RAG judge | `ministral-3:8b` | 95% | Primary metric |
| Fast classification | `ministral-3:14b` | 69% | Primary metric |
| text_to_sql | `qwen3.5:cloud` | 54% | Primary metric |

## What changed vs v3 (judge-driven)

| Stage | v3 judge winner | v5 GT winner | Changed? |
|---|---|---|---|
| emotion_shift | ministral-3:14b | ministral-3:14b | No |
| process_adherence | qwen3.5:cloud | kimi-k2.6:cloud | Yes |
| nli_policy | kimi-k2.5:cloud | ministral-3:8b | Yes |
| rag_judge | ministral-3:8b | ministral-3:8b | No |
| text_to_sql | qwen3.5:cloud | qwen3.5:cloud | No |
| fast_classification | ministral-3:14b | ministral-3:14b | No |

## process_adherence finding

F1-based GT scoring **confirms models genuinely struggle** on process_adherence (mean F1=0.32, exact-match=26%, judge avg=5.20). Low scores are not primarily a judge artifact.

## Unparseable responses (>10% threshold)

- emotion_shift/ministral-3:14b: 26% unparseable
- emotion_shift/kimi-k2.5:cloud: 52% unparseable
- emotion_shift/kimi-k2.6:cloud: 82% unparseable
- process_adherence/ministral-3:14b: 58% unparseable
- process_adherence/ministral-3:8b: 58% unparseable
- process_adherence/kimi-k2.5:cloud: 18% unparseable
- process_adherence/qwen3.5:cloud: 31% unparseable

## Largest judge vs ground-truth divergences

### process_adherence / ministral-3:14b / pa_060
- Old judge: **20.0** | GT score: **0.0** (unparseable)
- Reference: No missing SOP steps. Complete adherence.
- GT details: extraction_error: unparseable JSON
- Judge said: The model's response demonstrates significant deviations from the reference answer, failing to identify missing SOP steps and exhibiting numerous hallucinations and inaccuracies in its assessment, res

### process_adherence / ministral-3:14b / pa_055
- Old judge: **15.0** | GT score: **0.0** (unparseable)
- Reference: Missing SOP steps: [Acknowledge billing concern, Verify account and charge details, Explain charge source or correction].
- GT details: extraction_error: unparseable JSON
- Judge said: The model demonstrates significant gaps in adherence to SOP steps, particularly in verification, explanation, and escalation, resulting in a score of 15 and failing to meet the requirements for a pass

### emotion_shift / ministral-3:14b / es_001
- Old judge: **10.0** | GT score: **0.0** (no_match)
- Reference: No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.
- GT details: false positive shift
- Judge said: The model correctly identifies the cross-modal contradiction, provides specific quotes ('I am thrilled this happened again, amazing service' and 'anger'), and accurately classifies the type as a text-

### emotion_shift / kimi-k2.5:cloud / es_001
- Old judge: **10.0** | GT score: **0.0** (no_match)
- Reference: No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.
- GT details: legacy emotion label Sarcasm; use friction_root_cause
- Judge said: The model correctly identifies the cross-modal contradiction (sarcasm), provides a relevant quote ('I am thrilled this happened again, amazing service.'), and accurately explains the mismatch between 

### emotion_shift / kimi-k2.6:cloud / es_001
- Old judge: **10.0** | GT score: **0.0** (no_match)
- Reference: No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.
- GT details: legacy emotion label Sarcasm; use friction_root_cause
- Judge said: The model correctly identifies the cross-modal contradiction (sarcasm), provides specific quotes ('thrilled', 'amazing service') and 'anger', and accurately explains the mismatch between positive text

## Appendix: Judge scores (secondary / subjective)

Judge scores from v3 retained for transparency only — not used for recommendations above.

| Stage | Model | Old judge avg | GT exact match | GT score avg |
|---|---|---:|---:|---:|
| emotion_shift | kimi-k2.5:cloud | 6.56 | 13% | 1.29 |
| emotion_shift | kimi-k2.6:cloud | 5.75 | 7% | 0.71 |
| emotion_shift | ministral-3:14b | 7.31 | 15% | 1.47 |
| process_adherence | kimi-k2.5:cloud | 5.34 | 30% | 4.04 |
| process_adherence | kimi-k2.6:cloud | 5.51 | 43% | 5.46 |
| process_adherence | ministral-3:14b | 4.15 | 12% | 1.22 |
| process_adherence | ministral-3:8b | 4.36 | 12% | 1.23 |
| process_adherence | qwen3.5:cloud | 6.65 | 35% | 4.30 |
| nli_policy | kimi-k2.5:cloud | 8.73 | 60% | 6.05 |
| nli_policy | kimi-k2.6:cloud | 8.70 | 59% | 5.93 |
| nli_policy | ministral-3:8b | 8.70 | 70% | 6.98 |
| rag_judge | kimi-k2.6:cloud | 8.18 | 81% | 9.03 |
| rag_judge | ministral-3:8b | 9.36 | 95% | 9.73 |
| text_to_sql | kimi-k2.6:cloud | 5.60 | 38% | 5.60 |
| text_to_sql | ministral-3:8b | 2.96 | 20% | 2.96 |
| text_to_sql | qwen3.5:cloud | 6.48 | 54% | 6.48 |
| fast_classification | kimi-k2.6:cloud | 8.18 | 68% | 8.12 |
| fast_classification | ministral-3:14b | 8.44 | 69% | 8.25 |
| fast_classification | ministral-3:8b | 8.28 | 68% | 8.05 |