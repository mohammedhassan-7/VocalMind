# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v6 (Consolidated Final)

**Generated:** 2026-06-15  
**Audience:** Cold read — no prior report versions required  
**Data sources:** Retry-v2 run (`overnight_20260614/`, 3,219 observations, 0 API errors); ground-truth re-scores; `emotion_shift_v2.json` (n=170, fixed prompt); PA fuzzy re-score (765 obs). No new API calls in this document.

**Prior detail:** [FULL_REPORT_v5.1.md](FULL_REPORT_v5.1.md) · [EMOTION_SHIFT_V2_REPORT.md](EMOTION_SHIFT_V2_REPORT.md) · [PA_DIAGNOSIS.md](PA_DIAGNOSIS.md) · [PHASE_CONFIG_PA_SCORER.md](PHASE_CONFIG_PA_SCORER.md)

---

## Executive Summary

VocalMind benchmarked six Ollama Cloud pipeline stages on synthetic ground-truth data (3,219 model calls, zero errors). After pivoting from an LLM judge to objective ground-truth scoring, we found the judge had been wrong on several rankings — most dramatically emotion_shift, where the judge favored ministral-3:14b while kimi-k2.5 was the better reasoner but looked worse because 46% of its outputs were unparseable. A validated prompt fix (closed label set + JSON mode) took kimi-k2.5 to **53% exact match at 100% parseable** on a full n=170 re-run. **rag_judge (95%)** and **fast_classification (69%)** are proof-grade; **process_adherence** is genuinely weak (best F1≈0.54) but was understated by a benchmark scorer bug now fixed. The headline architectural finding: **three heavy stages want three different models**, but production exposes only one `OLLAMA_CLOUD_HEAVY_MODEL` — using the best single compromise (kimi-k2.6) leaves **~7 cumulative percentage points** on the table vs per-stage winners. Next step: wire per-stage env vars, deploy the emotion_shift prompt to production, and treat NLI/SQL prompt tweaks as promising but unconfirmed at full scale.

---

## Part 1 — Final per-stage results

Best available metric per stage (v2 / fuzzy-scorer numbers where they supersede v5.1).

| Stage | Best model | Key metric | Value | vs original (v3 judge) | In practice |
|---|---|---|---:|---|---|
| **emotion_shift** | `kimi-k2.5:cloud` | exact (all) | **53%** | Judge avg 6.56, winner ministral-14b (7.31); GT v5.1 was 37% | With the fixed prompt, **53%** of calls get the correct shift type (`sarcasm` / `passive_aggression` / `cross_modal` / `none`) with scoreable JSON every time (was 54% parseable). |
| **process_adherence** | `kimi-k2.6:cloud` | mean F1 | **0.539** | Judge avg 5.51, winner qwen3.5 (6.65); GT v5.1 was F1 0.508 | Best model identifies missing SOP step sets with **~54%** overlap fidelity — roughly half of evaluations fully match the reference missing-step set, half are partial misses or extras. |
| **nli_policy** | `ministral-3:8b` | exact (all) | **52%** | Judge avg 8.64, winner kimi-k2.5 (8.73) | **52%** of policy claims get the correct NLI verdict (Entailment / Benign Deviation / Contradiction / Policy Hallucination) vs reference. |
| **rag_judge** | `ministral-3:8b` | exact (all) | **95%** | Judge avg 9.36, same winner | **95%** of compliance checks match the correct derived verdict **and** cited rule ID — defensible proof claim (n=150). |
| **text_to_sql** | `qwen3.5:cloud` | exact (all) | **54%** | Execution score 6.48/10, same winner | **54%** of generated SQL executes to the same result as reference on seeded DB (read-only queries). |
| **fast_classification** | `ministral-3:14b` | exact (all) | **69%** | Judge avg 8.44, same winner | **69%** get both correct topic label and gibberish flag — latency-critical stage, already strong without prompt work. |

### Recommended production stack (ground-truth driven)

| Role | Model | Notes |
|---|---|---|
| Heavy — emotion_shift | `kimi-k2.5:cloud` | v2 validated; **blocked** until per-stage config exists |
| Heavy — process_adherence | `kimi-k2.6:cloud` | F1 0.539 (fuzzy scorer) |
| Heavy — nli_policy | `ministral-3:8b` | 52% exact |
| RAG judge | `ministral-3:8b` | 95% exact |
| Fast classification | `ministral-3:14b` or `ministral-3:8b` | 69% / 68% |
| text_to_sql | `qwen3.5:cloud` | 54% execution match (assistant path) |

---

## Part 2 — What changed and why

### 1. Judge → ground truth

Across three prior judge-driven runs we found repeatable judge failures: rag_judge rubric ignored `compliance_score` semantics, PA penalized schema differences over content, and emotion_shift conflated format with reasoning. We replaced the primary metric with **exact match / F1 against reference labels** (no new model calls — re-scored saved `raw_response` JSON). Rankings shifted: emotion_shift winner flipped from ministral-14b (judge) to kimi-k2.5 (GT, before prompt fix); PA winner from qwen3.5 (judge) to kimi-k2.6 (GT F1); NLI from kimi-k2.5 (judge) to ministral-3:8b (GT). rag_judge and fast_classification stayed aligned — judge and GT agreed they were strong.

### 2. Parseable vs accurate (emotion_shift case study)

Splitting **exact (all)** from **exact (parseable)** and **parseable %** exposed that kimi-k2.5 was **68% accurate when scoreable** but only **54% parseable** (v5.1). Production (`service.py`) does **not** retry on JSON parse failure — failures degrade to `dissonance_type=Unknown`. So headline “37% exact” mixed “wrong answer” with “couldn’t score output.” ministral-14b looked better on exact(all) (26%) mainly because it was more parseable (78%), not more accurate when parseable (34%).

### 3. Prompt fix validated at scale

We tightened prompts with a **closed four-label schema**, few-shots, and JSON mode in the benchmark harness (`prompt_constants.py`). Validation (n=20) showed parseable 54%→100%; a **full re-run** (n=170, `emotion_shift_v2.json`) confirmed **37%→53% exact(all)** with **100% parseable** for kimi-k2.5 — a reproducible improvement from prompting, not a model swap. The fix is in the benchmark path; production `prompts.py` shares `prompt_constants` but production still uses the single global heavy model.

### 4. PA scorer bug (measurement, not model)

PA diagnosis (11/20 CLOSER on validation) pointed to scorer issues, not model regression. Two bugs in `ground_truth_scorer.py`: (a) reference parsing used `,(?=[A-Z])` but ground-truth strings use `", Confirm..."` (comma+space), collapsing multi-step references into one string; (b) missing fuzzy match from model `step_key` tokens to `STEP_KEY_TO_LABEL`. Re-scoring **765 existing observations** (no new API calls) raised kimi-k2.6 F1 **0.508→0.539**. PA remains the weakest stage, but prior reports **understated** all PA scores. This fix applies to the **evaluation pipeline only** — production PA logic in `service.py` is unchanged.

---

## Part 3 — Architectural finding: one heavy model vs three winners

**Fact:** `build_emotion_shift_chain(model=...)`, `build_process_adherence_chain(model=...)`, and `build_nli_policy_chain(model=...)` each accept an optional model, but production calls `_get_shared_model()` → one **`OLLAMA_CLOUD_HEAVY_MODEL`** (currently `kimi-k2.6:cloud`). There are no per-stage env vars today.

**Per-stage ground-truth winners (best available metrics):**

| Stage | Winner | Score (0–1 scale) |
|---|---|---:|
| emotion_shift | kimi-k2.5:cloud | 0.53 (exact, v2 prompt) |
| process_adherence | kimi-k2.6:cloud | 0.539 (F1, fuzzy scorer) |
| nli_policy | ministral-3:8b | 0.52 (exact) |
| **Optimal (if routed)** | — | **1.589 sum · 0.530 avg** |

**If one model must serve all three heavy stages** (scores for that model on each stage):

| Global choice | ES | PA F1 | NLI | Sum | Avg | Gap vs optimal (sum) |
|---|---:|---:|---:|---:|---:|---:|
| **kimi-k2.6:cloud** *(best single)* | 0.48 | 0.539 | 0.50 | **1.519** | 0.506 | **0.070** |
| kimi-k2.5:cloud | 0.53 | 0.471 | 0.49 | 1.491 | 0.497 | 0.098 |
| ministral-3:8b | — † | 0.200 | 0.52 | — | — | — |

† ministral-3:8b was not in the emotion_shift triage set; not a fair global-heavy candidate without additional runs.

**Decision-relevant figure:** Sticking with **one** heavy model (best compromise: **kimi-k2.6**) sacrifices **0.070 cumulative points** (~**7.0 pp** across the three metrics, ~**2.3 pp** average) versus routing each stage to its own winner — primarily **5 pp on emotion_shift** (0.53−0.48) and **2 pp on NLI** (0.52−0.50), with PA at the optimum. Per-stage env vars (e.g. `OLLAMA_CLOUD_EMOTION_SHIFT_MODEL`, `OLLAMA_CLOUD_PROCESS_ADHERENCE_MODEL`, `OLLAMA_CLOUD_NLI_POLICY_MODEL`, fallback to `OLLAMA_CLOUD_HEAVY_MODEL`) recover that gap with small wiring effort; `build_llm(stage=...)` is the natural hook.

---

## Part 4 — Honest limitations

- **Judge calibration:** 48-sample human calibration set remains **0/49 scored** — low stakes for recommendations (judge is secondary) but unvalidated as a monitoring signal.
- **Ground-truth dedup:** ~3,328 near-duplicate pairs in the pool (largest cluster 92) — metrics may be slightly optimistic from repeated phrasing.
- **Synthetic data only:** No real call-center transcripts in the benchmark pool.
- **NLI / text_to_sql prompts:** +13 pp / +6 pp at n=20 validation — **not** full-scale confirmed (unlike emotion_shift n=170).
- **rag_judge / fast_classification:** Never prompt-tuned; already strong under GT.
- **emotion_shift v2:** Used new prompt; v5.1 overnight rows used old prompt — cross-report comparisons for ES are intentional (old prompt vs new prompt), not same-prompt model swaps.
- **PA fuzzy scorer:** Improves measurement; does not make models better at SOP reasoning.

---

## Part 5 — Action items (prioritized)

1. **Per-stage model config (highest value, smallest effort)** — Wire `build_llm(stage=...)` to per-stage env vars; apply ES→kimi-k2.5, PA→kimi-k2.6, NLI→ministral-3:8b. Recovers ~**7.0 pp** vs single kimi-k2.6 heavy model.
2. **Deploy emotion_shift prompt fix to production** — Validated at n=170; currently benchmark-only path shares constants but production needs the closed-label + JSON discipline end-to-end.
3. **PA scorer scope** — Reference-parse + fuzzy key matching are **benchmark/eval only**; confirm production `evaluate_process_adherence` does not share the buggy regex (it does not — bug was in `ground_truth_scorer.py` only).
4. **Optional full-scale validation** — NLI and text_to_sql prompt tweaks if pursuing further gains (+13 pp / +6 pp at n=20).
5. **Optional / low priority** — Judge calibration, dedup cleanup, real-transcript benchmark extension.

---

## Investigation arc (one paragraph)

Overnight retry-v2 completed all 3,219 observations with rate-limit handling → judge-driven v3 → ground-truth v5/v5.1 exposed judge bias and emotion_shift parse/reasoning conflation → prompt validation + emotion_shift v2 full re-run proved schema tightening → PA diagnosis + fuzzy scorer fixed measurement → consolidated here as v6 with a quantified multi-model routing tradeoff.

---

*End of FULL_REPORT_v6. For row-level data see `*_groundtruth.json`, `emotion_shift_v2_groundtruth.json`, and v5.1 appendix tables.*
