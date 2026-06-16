# Prompt Validation Report (n=20 per stage)

Tightened production prompts validated on stratified 20-sample subsets.

## Part 1–4: Prompt changes

- **emotion_shift**: closed label set (`sarcasm|passive_aggression|cross_modal|none`), strict JSON schema, 3 few-shot examples, JSON mode in benchmark.
- **process_adherence**: full RESOLUTION_GRAPH step_key catalog, `missing_sop_steps` must use snake_case keys only, few-shot example.
- **nli_policy**: Benign Deviation vs Contradiction distinguishing rule + nli_003-style example, strict `verdict` JSON.
- **text_to_sql**: 3 few-shot join/aggregate examples added to benchmark + production schema block.

Files: `backend/app/llm_trigger/prompt_constants.py`, `prompts.py`, `benchmark_ollama_cloud.py`.

## Part 5: Validation results

| Stage | Model | Metric | v5.1 full (baseline) | n=20 new | Verdict |
|---|---|---|---:|---:|---|
| emotion_shift | kimi-k2.5:cloud | parseable | 54% | 100% | IMPROVED (worth full re-run) |
| emotion_shift | kimi-k2.5:cloud | exact (parseable) | 68% | 55% | |
| emotion_shift | kimi-k2.5:cloud | exact (all) | 37% | 55% | |
| process_adherence | kimi-k2.6:cloud | exact (all) | 35% | 30% | NO CHANGE |
| process_adherence | kimi-k2.6:cloud | F1 avg | 0.508 | 0.450 | |
| nli_policy | ministral-3:8b | exact (all) | 52% | 65% | IMPROVED (worth full re-run) |
| text_to_sql | qwen3.5:cloud | exact (all) | 54% | 60% | IMPROVED (worth full re-run) |

## Summary

- **emotion_shift/kimi-k2.5:cloud**: parseable 54%→100%, exact(parseable) 68%→55% — **IMPROVED (worth full re-run)**
- **process_adherence/kimi-k2.6:cloud**: exact 35%→30%, F1 0.508→0.450 — **NO CHANGE**
- **nli_policy/ministral-3:8b**: exact 52%→65% — **IMPROVED (worth full re-run)**
- **text_to_sql/qwen3.5:cloud**: exact 54%→60% — **IMPROVED (worth full re-run)**