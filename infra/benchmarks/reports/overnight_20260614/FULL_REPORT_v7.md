# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v7

**Generated:** 2026-06-15  
**Audience:** Cold read — supersedes FULL_REPORT_v6  
**Data sources:** Recomputed from checkpoints — see `LEADERBOARD_VALIDATION_v7.md` (deduped one row per model+sample_id). ES v2 n=170/model; NLI n=172/model (not 344).

---

## Changelog vs v6

1. **Production json_mode (Prompt 16):** `build_emotion_shift_chain`, `build_nli_policy_chain`, and `build_process_adherence_chain` now bind `response_format={"type": "json_object"}` on ChatOpenAI (Ollama Cloud OpenAI-compatible API). `langchain_ollama` is not installed; native Ollama `format=` is not used.
2. **PA scoring (Prompt 17):** `ground_truth_scorer.extract_pa_predicted_missing` reads top-level `missing_sop_steps` when present, otherwise derives missing steps from structured `evaluation` blocks (`justifications`, `sop_compliance`, `steps`, `step_evaluations`, etc.) using checkpoint-derived adherence/status vocabulary (`missing`, `partial`, `deviated`, …). Entries without a recognizable shape return an explicit extraction error (scored F1=0). **PA routing uses F1 over all n (errors_as_0), not mean-F1 excluding extraction errors** — the latter wrongly favored qwen3.5 (31% extract errors). **gemma3:12b judge score is NOT used for PA** (calibration r=0.0642, MAE=1.625).
3. **Per-stage routing (Prompt 18):** `OLLAMA_EMOTION_SHIFT_MODEL`, `OLLAMA_PROCESS_ADHERENCE_MODEL`, `OLLAMA_NLI_MODEL` added with fallback to `OLLAMA_CLOUD_HEAVY_MODEL`; `get_model_for_stage()` in `chains.py`.
4. **NLI/SQL baseline (Prompt 19):** No full-population pre-tweak checkpoint exists; overnight run already used current `prompt_constants.py`. n=20 validation gains (+13 pp NLI, +6 pp SQL) are **not confirmed** at full scale. Full-population GT pass rates below are the authoritative numbers for v7.
5. **ES offline parse (Prompt 22):** Old `emotion_shift.checkpoint.jsonl` responses use legacy field names → 0% strict `EmotionShiftAnalysis` parse; v2 checkpoint → ~100% strict parse. **Live json_mode (Prompt 24):** 5/5 parse OK per stage (ES/PA/NLI) with `response_format={"type": "json_object"}` confirmed.
6. **Production prompt fix:** JSON schema braces in `prompt_constants.py` escaped for LangChain templates (fixed `ValueError: Nested replacement fields` that blocked all live chain calls).
7. **NLI strict parse (Prompt 23):** Overnight checkpoint uses `category` not `nli_category` → 100% strict failure offline; live production chains with format_instructions parse 5/5. `NLIEvaluation` accepts `verdict`/`category` aliases.

---

## Executive Summary

After judge calibration (48 samples, overall r=0.8893), PA judge scores are discarded for model selection. Production chains now request JSON object mode. Per-stage GT winners: **emotion_shift** `kimi-k2.5:cloud` (53% exact, v2 prompt), **process_adherence** `kimi-k2.6:cloud` (F1=0.546 errors_as_0), **nli_policy** `ministral-3:8b` (52% exact), **rag_judge** `ministral-3:8b` (95%), **text_to_sql** `qwen3.5:cloud` (54%), **fast_classification** `ministral-3:14b` (69%).

---

## How to verify these numbers

All leaderboard values are recomputed from overnight checkpoints (one row per model+sample_id, 
last checkpoint line wins). No judge scores used for winners except where noted unreliable.

```bash
python infra/scripts/validate_leaderboard_v7.py      # offline, no API
python infra/scripts/run_production_gt_validation.py  # live production chains vs GT
```

See `LEADERBOARD_VALIDATION_v7.md` for full per-model tables matching this report.

**Live spot-check (production chains):** `run_production_gt_validation.py` runs 15 evenly-spaced 
GT samples per stage (manifest in `validation_manifest_v7.json`) through the same chains shipped in 
`chains.py`, then scores with `ground_truth_scorer`. Expect parse OK ≈100%; GT exact on a 15-sample slice 
will vary (~40–60% is normal when full-population exact is ~50%). Low exact % is **task difficulty**, not a 
measurement bug — offline validation confirms every v7 winner claim matches checkpoint recomputation.

---

## Leaderboard — all 6 axes

| Stage | Best model | Primary metric | Value | GT pass (full pop.) | Judge avg (best) | Notes |
|---|---|---|---:|---:|---:|---|
| emotion_shift | `kimi-k2.5:cloud` | exact (v2, n=170) | **53%** | — | — | Judge trusted (cal r=1.0); production json_mode shipped |
| process_adherence | `kimi-k2.6:cloud` | mean GT F1 (errors_as_0) | **0.546** | — | unreliable | Judge r=0.064 — use F1 incl. errors |
| nli_policy | `ministral-3:8b` | exact (all) | **52%** | **52%** | trusted | No pre-tweak full baseline |
| rag_judge | `ministral-3:8b` | exact (all) | **95%** | **95%** | trusted | Unchanged |
| text_to_sql | `qwen3.5:cloud` | execution exact | **54%** | **54%** | trusted | No pre-tweak full baseline |
| fast_classification | `ministral-3:14b` | exact (all) | **69%** | **69%** | all-agree | Unchanged |

### emotion_shift — per model (v2 prompt, n=170)

| Model | Exact % | Parseable % | n |
|---|---:|---:|---:|
| kimi-k2.5:cloud | 53% | 100% | 170 |
| ministral-3:14b | 48% | 100% | 170 |
| kimi-k2.6:cloud | 48% | 100% | 170 |

### process_adherence — per model (GT F1; **routing uses F1_incl_errors**) 

| Model | F1 incl errors | F1 excl errors | exact % | extraction errors | n |
|---|---:|---:|---:|---:|---:|
| kimi-k2.6:cloud | 0.546 | 0.572 | 43% | 7 | 153 |
| qwen3.5:cloud | 0.430 | 0.621 | 35% | 47 | 153 |
| kimi-k2.5:cloud | 0.404 | 0.494 | 30% | 28 | 153 |
| ministral-3:8b | 0.123 | 0.293 | 12% | 89 | 153 |
| ministral-3:14b | 0.122 | 0.291 | 12% | 89 | 153 |

> **F1 excl errors** (old, misleading): qwen3.5=0.621 on 106/153 entries. **F1 incl errors** (routing metric): kimi-k2.6=0.546 wins.


### nli_policy — per model

| Model | Exact % | n |
|---|---:|---:|
| ministral-3:8b | 52% | 172 |
| kimi-k2.5:cloud | 49% | 172 |
| kimi-k2.6:cloud | 49% | 172 |

### rag_judge — per model

| Model | Exact % | n |
|---|---:|---:|
| ministral-3:8b | 95% | 150 |
| kimi-k2.6:cloud | 81% | 150 |

### text_to_sql — per model

| Model | Exact % | n |
|---|---:|---:|
| qwen3.5:cloud | 54% | 50 |
| kimi-k2.6:cloud | 38% | 50 |
| ministral-3:8b | 20% | 50 |

### fast_classification — per model

| Model | Exact % | n |
|---|---:|---:|
| ministral-3:14b | 69% | 154 |
| kimi-k2.6:cloud | 68% | 154 |
| ministral-3:8b | 68% | 154 |

---

## Recommended per-stage production models

| Env var | Winner | Metric |
|---|---|---|
| `OLLAMA_EMOTION_SHIFT_MODEL` | `kimi-k2.5:cloud` | 53% exact (v2) |
| `OLLAMA_PROCESS_ADHERENCE_MODEL` | `kimi-k2.6:cloud` | F1 0.546 (errors_as_0) |
| `OLLAMA_NLI_MODEL` | `ministral-3:8b` | 52% exact |
| `OLLAMA_CLOUD_FAST_MODEL` | `ministral-3:8b` or `ministral-3:14b` | RAG 95% / FC 69% |

---

## Prompt v8 — failure-driven fixes (2026-06-15)

Root-cause analysis: `FAILURE_ANALYSIS_v7.md`. Changes: `PROMPT_V8_CHANGES.md`.

**Live validation (same 15-sample manifest, production chains):**

| Stage | v7 exact | v8 exact | Δ |
|---|---:|---:|---:|
| emotion_shift (kimi-k2.5) | 4/15 (27%) | **7/15 (47%)** | +20 pp |
| nli_policy (ministral-3:8b) | 7/15 (47%) | **10/15 (67%)** | +20 pp |
| process_adherence (kimi-k2.6) | 7/15 (47%) | 8/15 (53%) | +6 pp |

Full-population leaderboard above is still from overnight checkpoints (pre-v8). Re-run `benchmark_ollama_cloud.py` on ES+NLI to refresh official GT rates after shipping v8 prompts.

See `LIVE_GT_VALIDATION_v8.md` for per-sample results.

---

*End of FULL_REPORT_v7. Generator: `infra/scripts/generate_full_report_v7.py`.*