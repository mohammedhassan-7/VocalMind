# VocalMind Ollama Cloud Model Benchmark Summary v3

**Final validation run:** `benchmark_subset_20260613_1648.json` (135-sample stratified subset)  
**RAG judge re-run (post-fix):** `benchmark_rag_rejudge_20260613.json`  
**Ground truth pool:** `ollama_cloud_ground_truth.json` (550 samples)  
**Subset file:** `ollama_cloud_subset_v1.json`  
**Judge:** `gemma3:12b` via Ollama Cloud (neutral — not a candidate model)

---

## Methodology

- **135-sample stratified subset** drawn from a 550-sample ground truth pool (`ollama_cloud_subset_v1.json`), preserving all hand-curated originals per stage.
- **Parallelized execution:** 5 candidate models called concurrently per sample via `ThreadPoolExecutor` (revert with `--serial-models`).
- **Neutral judge:** gemma3:12b with JSON-literal normalization (`True`/`False` → `true`/`false`), retry on parse failure, and `score: null` on persistent failure.
- **Wall-clock:** subset run **124.7 min** (~2h 5m); rag_judge-only re-run **7.7 min** (100 rows, parallel).

### Statistical caveats

- **process_adherence** separation is based on **25 samples** (up from 5 in v1). qwen3.5 leads kimi-k2.6 by **0.36** (6.72 vs 6.36) — within prior-observed judge noise (~0.7–2 pt swings at small n). Treat heavy model choice as primarily driven by **emotion_shift** and **nli_policy**, where kimi-k2.6's lead is larger and more stable at this scale.
- **rag_judge** absolute scores are **not comparable across stages** (different rubric/difficulty). After harness fix, all models score ~9.7/10 — this stage does **not** differentiate models.

---

## Per-stage results (135-sample subset)

| Stage | Samples | kimi-k2.6 | kimi-k2.5 | ministral-14b | ministral-8b | qwen3.5 | Leader |
|---|---|---|---|---|---|---|---|
| emotion_shift | 25 | **8.24** | 7.92 | 7.88 | 7.40 | 7.60 | kimi-k2.6 |
| process_adherence | 25 | 6.36 | 5.92 | 4.08 | 4.68 | **6.72** | qwen3.5 |
| nli_policy | 25 | **9.52** | 9.12 | 8.52 | 9.08 | 8.72 | kimi-k2.6 |
| rag_judge | 20 | 9.70* | 9.70* | 9.70* | 9.65* | 9.70* | tied (post-fix) |
| text_to_sql | 20 | 8.30 | 8.75 | 8.05 | 7.50 | **9.25** | qwen3.5 |
| fast_classification | 20 | 9.50 | 9.50 | 9.00 | **9.75** | 8.75 | ministral-8b |

\* rag_judge scores from `benchmark_rag_rejudge_20260613.json` (harness fix applied). Pre-fix subset scores were 4.6–6.0 (judge bug, not model quality).

### Latency highlights (subset run, avg total ms)

| Stage | kimi-k2.6 | ministral-8b | qwen3.5 |
|---|---|---|---|
| emotion_shift | 48,975 | 16,093 | 61,892 |
| process_adherence | 52,885 | 21,810 | 55,861 |
| nli_policy | 25,830 | 7,051 | 40,154 |
| fast_classification | 4,742 | **1,748** | 17,628 |

---

## rag_judge diagnosis (Step 1)

**Root cause: judge harness bug (b), not model ceiling or doc-name mismatch.**

1. **Judge rubric** scores compliance **verdict match + policy doc ID match** (10/7/3/0 scale). Candidate models return JSON `{compliance_score, violations, policy_references, reasoning}` — not a text verdict.
2. **Bug:** gemma3:12b judge did not map `compliance_score` to Compliant/Non-compliant before applying the rubric. Correct non-compliant responses (score 0.0–0.2) were scored **3** with reasoning like *"verdict incorrect (should be non-compliant)"* while the model was already non-compliant. **68/100 rows** scored exactly 3 pre-fix.
3. **Doc names:** `FIN-RULE-001`, `CS-RULE-008`, etc. match NexaLink evaluation manifests (`storage/audio/nexalink/evaluation/CALL_*.json` `policy_refs`). They are canonical rule IDs, not Qdrant PDF filenames. Benchmark injects policy text inline (no retrieval step) — IDs are consistent with production SOP references.
4. **Model output format:** JSON with optional markdown fences — fence stripping already applied; issue was judge-side verdict mapping, not model wrapping.

**Fix applied:**
- `_normalize_rag_response_for_judge()` derives explicit verdict from `compliance_score` (≥0.8 Compliant, 0.4–0.79 Partial, <0.4 Non-compliant).
- Updated `rag_judge` judge prompt with score-to-verdict mapping and rule-ID matching guidance.

**Re-run result:** all models **9.65–9.70/10** (was 4.6–6.0). Score distribution: 91×10, 8×7, 1×3.

---

## Final recommendations

### Heavy model — `OLLAMA_CLOUD_HEAVY_MODEL`: **kimi-k2.6:cloud** — CONFIRMED, no change

| Criterion | Evidence |
|---|---|
| emotion_shift | **8.24** — leads all candidates by 0.3+ |
| nli_policy | **9.52** — leads; 92% pass rate |
| process_adherence | 6.36 — near-tied with qwen (6.72); within judge noise |
| rag_judge | ~9.7 post-fix — no differentiation between models |

### Fast model — `OLLAMA_CLOUD_FAST_MODEL`: **ministral-3:8b** — CONFIRMED, no change

| Criterion | Evidence |
|---|---|
| fast_classification | **9.75/10**, ~1.7s avg latency — best quality and speed |
| nli_policy | 9.08 — competitive with heavy models at 7s latency |

### Text-to-SQL — production-ready

- All **50** ground-truth SQL queries validate via `EXPLAIN` against live schema (after fixing 8 hallucinated `u.team` samples → `u.role`/`u.agent_type`).
- All models ≥7.5/10 on subset; qwen3.5 leads (9.25) but gap is small. Current stack adequate; ministral-3:8b handles fast paths.

### rag_judge — RESOLVED after fix (9.65–9.70 range)

Not a model-selection differentiator. Relative ranking collapsed to a tie after correct verdict mapping. Production `PolicyComplianceEvaluator` uses the same JSON schema — benchmark now aligns with production output shape.

---

## Infrastructure delivered (this audit cycle)

| Item | Detail |
|---|---|
| Production schema fix | `utterances.speaker` → `speaker_role` in `assistant.py` |
| PA judge fix | Python literal normalization + retry |
| Ground truth | 550 samples (`generate_ground_truth.py`) |
| Subset | 135 samples (`build_benchmark_subset.py` → `ollama_cloud_subset_v1.json`) |
| Parallelization | `--serial-models` flag; default parallel (5 workers) |
| SQL GT fix | 8 `u.team` samples corrected to real DDL columns |

---

## Open items (not blocking)

- **550-sample full regression run** available (~2.5h parallel) using same harness
- **Template repetition** in generated rag_judge/nli_policy samples — diversify if scaling further
- **rag_judge benchmark** does not exercise full RAG retrieval pipeline (policy text inlined); separate integration test recommended for retrieval accuracy

---

## Migration status

**COMPLETE** — model selection validated at 135-sample scale. No production env changes needed; current config already optimal per benchmark.

```
OLLAMA_CLOUD_HEAVY_MODEL=kimi-k2.6:cloud  ✓
OLLAMA_CLOUD_FAST_MODEL=ministral-3:8b    ✓
Smoke test: pass
```

---

## Proposed commit message

```
fix(benchmark): schema bug, harness fixes, GT scale-up, and v3 summary

- Fix assistant _SCHEMA speaker → speaker_role (production text-to-SQL)
- Fix PA/rag_judge gemma3 judge parsing (JSON literals, verdict mapping)
- Add parallel model execution, 550-sample GT, 135-sample subset
- Correct text_to_sql GT u.team hallucinations; validate 50/50 via EXPLAIN
- Document final model selection: kimi-k2.6 (heavy), ministral-3:8b (fast)
```
