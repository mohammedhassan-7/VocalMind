# Prompt v8 — failure-driven fixes

**Based on:** `FAILURE_ANALYSIS_v7.md` (checkpoint confusion matrices)

## emotion_shift (kimi-k2.5) — top failures fixed in prompt

| Confusion | Count | Fix |
|---|---:|---|
| passive_aggression → none | 37 | Agent + customer PA scope; read `Acoustic note:`; decision order; Examples D/E |
| cross_modal → passive_aggression | 13 | Clearer decision order (PA before cross_modal) |
| cross_modal → sarcasm | 9 | Sarcasm requires positive lexical tone |

**Input normalization:** `benchmark_input.normalize_emotion_shift_input()` extracts agent/customer/acoustic from transcript chunks for production chains and future benchmarks.

## nli_policy (ministral-3:8b) — top failures fixed in prompt

| Confusion | Count | Fix |
|---|---:|---|
| Policy Hallucination → Contradiction | 38 | Classification order: hallucination BEFORE contradiction; invented fee example |
| Benign Deviation → Contradiction | 21 | At-threshold $50 rule; Example E (nli_013 pattern) |

## Files changed

- `backend/app/llm_trigger/prompt_constants.py` — ES/NLI rubric + few-shots
- `backend/app/llm_trigger/prompts.py` — ES task instructions
- `infra/scripts/benchmark_input.py` — shared GT input normalizer
- `infra/scripts/benchmark_ollama_cloud.py` — normalized user messages for ES/NLI
- `infra/scripts/run_production_gt_validation.py` — v8 output + normalized parse

## Validate

```bash
python infra/scripts/analyze_stage_failures.py
python -u infra/scripts/run_production_gt_validation.py   # → LIVE_GT_VALIDATION_v8.md
```

Full-population improvement requires re-benchmark:

```bash
python infra/scripts/benchmark_ollama_cloud.py --stages emotion_shift,nli_policy --models kimi-k2.5:cloud,ministral-3:8b ...
```
