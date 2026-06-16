# VocalMind — emotion_shift Config + PA Fuzzy Scorer

**Generated:** 2026-06-15

---

## Part 1 — emotion_shift config

**Per-stage model override: does not exist**

`chains.py` exposes `build_emotion_shift_chain(model=...)` but production always uses `_get_shared_model()` → single `OLLAMA_CLOUD_HEAVY_MODEL`. Config (`config.py`, `.env`, `docker-compose.yml`) only defines:

- `OLLAMA_CLOUD_HEAVY_MODEL` — all heavy chains (emotion_shift, process_adherence, nli_policy)
- `OLLAMA_CLOUD_FAST_MODEL` — fast classification

**STOPPED — no global change made.** Setting `OLLAMA_CLOUD_HEAVY_MODEL=kimi-k2.5:cloud` would also affect PA and NLI where different models won.

### Three-way heavy-stage tradeoff

| Stage | Benchmark winner | Metric |
|---|---|---|
| **emotion_shift** | `kimi-k2.5:cloud` | 53% exact(all), 100% parseable (v2 n=170) |
| **process_adherence** | `kimi-k2.6:cloud` | F1=0.539 (post fuzzy scorer; was 0.508 v5.1) |
| **nli_policy** | `ministral-3:8b` | 52% exact |

**Finding:** Per-stage model selection requires a new config mechanism (e.g. `OLLAMA_CLOUD_EMOTION_SHIFT_MODEL`, or stage-aware `build_llm(stage=...)`). The optional `model` parameter on chain builders is the hook — env vars are not wired.

**be-test:** `uv run pytest tests/` — passed (backend suite).

---

## Part 2 — PA scorer fix

**Changes in `ground_truth_scorer.py`:**

1. **Reference parse fix:** `parse_pa_ref_missing` split regex `,(?=[A-Z])` → `,\s+(?=[A-Z])` (comma+space before capitalized step names).
2. **Fuzzy step_key matching:** `_fuzzy_match_step_key()` at threshold **0.85** against `STEP_KEY_TO_LABEL`; logged to `PA_FUZZY_MATCH_LOG`.

**20-sample validation (kimi-k2.6, new prompt responses):** mean F1 **0.450 → 0.568**

---

## Part 3 — CLOSER validation

Most CLOSER gains came from **reference parsing** (exact step_keys already mapped correctly). Fuzzy matching logged **16** matches on the 20-sample set.

**Over-matching (borderline 0.85–0.92):** 3 cases — all semantically correct:

| model_key (prose) | matched_key | sim |
|---|---|---:|
| Verify customer identity | verify_user_identity | 0.909 |
| Acknowledge fee concern | acknowledge_the_fee_concern | 0.92 |
| Verify account and fee details | verify_account_and_charge_details | 0.889 |

No false links like `verify_refund_eligibility` → `verify_account_eligibility` observed.

**Recommend full re-score:** yes

---

## Part 4 — Full PA re-score (765 obs, no new API calls)

| Model | v5.1 F1 | fuzzy F1 | v5.1 exact% | fuzzy exact% |
|---|---:|---:|---:|---:|
| **kimi-k2.6:cloud** | 0.508 | **0.539** | 35% | **37%** |
| kimi-k2.5:cloud | 0.443 | 0.471 | 33% | 37% |
| qwen3.5:cloud | 0.421 | 0.453 | 31% | 34% |
| ministral-3:8b | 0.192 | 0.200 | 6% | 7% |
| ministral-3:14b | 0.138 | 0.149 | 3% | 3% |

**Ranking unchanged.** kimi-k2.6 still leads; gap to qwen3.5 widened (0.421→0.453 vs kimi 0.508→0.539).

**New PA winner:** `kimi-k2.6:cloud` — F1=0.539

---

## Status

| Area | Status |
|---|---|
| **emotion_shift** | Blocked on per-stage config — kimi-k2.5 validated at 53%/100% parseable; needs `OLLAMA_CLOUD_*_PER_STAGE` mechanism |
| **PA** | Scorer fixed — F1 0.508→0.539 for kimi-k2.6 on full 765 obs; no prompt re-run needed |

Detail: `PA_FUZZY_VALIDATION.md`
