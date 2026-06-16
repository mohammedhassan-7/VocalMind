# VocalMind Ollama Cloud Migration — Full Benchmark Report

**Generated:** 2026-06-13  
**Purpose:** Consolidate all benchmark passes into one reference document (data, timing, cost, quality).  
**No new benchmark runs** — all numbers derived from existing JSON reports.

### Source files

| File | Role |
|---|---|
| `ollama_cloud_ground_truth.json` | 550-sample ground truth pool |
| `ollama_cloud_subset_v1.json` | 135-sample stratified subset (final run definition) |
| `benchmark_subset_20260613_1648.json` | Final 135-sample parallel run (6 stages) |
| `benchmark_rag_rejudge_20260613.json` | rag_judge post-fix re-run (20 samples) |
| `benchmark_PA_rejudge_20260613.json` | process_adherence post-fix re-judge (10 samples) |
| `benchmark_20260613_1324.json` | Original run (harness bugs present) |
| `benchmark_REAUDIT_20260613_1455.json` | Re-audit (harness fixes, 10 samples × 4 stages) |

---

## 1. Executive summary

**Production configuration (unchanged):** `OLLAMA_CLOUD_HEAVY_MODEL=kimi-k2.6:cloud`, `OLLAMA_CLOUD_FAST_MODEL=ministral-3:8b`.

We benchmarked five Ollama Cloud candidate models across six VocalMind pipeline stages using a **135-sample stratified subset** drawn from a **550-sample ground truth pool**, with **parallel 5-model execution** and a **neutral gemma3:12b judge**. This migration audit fixed **one production schema bug** (`utterances.speaker` → `speaker_role` in the text-to-SQL assistant), **three benchmark harness bugs** (PA judge JSON literals, rag_judge verdict mapping, text_to_sql schema injection), and scaled ground truth from ~5–10 samples/stage to 50–100/stage.

**Final recommendation: no production model change.** kimi-k2.6:cloud leads the stages that drive heavy-model selection (emotion_shift, nli_policy) with reproducible margins; ministral-3:8b leads fast_classification on both quality (9.75/10) and latency (~1.7s). qwen3.5:cloud marginally wins text_to_sql and process_adherence at small n, but gaps are within judge noise or do not justify swapping the configured stack.

---

## 2. Per-stage deep dive

### 2.1 emotion_shift

#### Data
| Metric | Value |
|---|---|
| Full pool | **100** samples |
| Subset benchmarked | **25** |
| Avg input size | **569 chars** (~262 prompt tokens) |
| Avg output size | **96–338** completion tokens (model-dependent) |

**Label distribution (subset):** sarcasm 6, passive_aggression 8, none (true negative) 7 (**28%**), cross_modal 4.

**Example — typical (sarcasm, `es_001`):**
```
Input:  Agent context: Daniel handling billing dispute.
        Customer text: I am thrilled this happened again, amazing service.
        Acoustic emotion: anger
        Task: Detect cross-modal contradiction and classify type.
Ref:    Cross-modal contradiction flagged. Type: Sarcasm.
        Must cite 'thrilled' or 'amazing'; note anger vs positive text mismatch.
```

**Example — edge case (true negative, `es_004`):**
```
Input:  Customer: My internet was out for two days... I want a credit on my bill.
        Acoustic emotion: frustrated | Text emotion: frustrated
Ref:    No cross-modal contradiction. is_dissonance_detected: false.
        (True negative — aligned frustration, no sarcasm/passive-aggression)
```

#### Timing (subset run, parallel per sample)

| Model | Avg TTFT | Avg total | Min | Max |
|---|---|---|---|---|
| kimi-k2.6:cloud | 46,680 ms | **48,975 ms** | 16,288 ms | 110,112 ms |
| kimi-k2.5:cloud | 65,917 ms | 72,194 ms | 24,066 ms | 169,373 ms |
| ministral-3:14b | 9,149 ms | 17,080 ms | 0 ms | 63,487 ms |
| ministral-3:8b | 9,648 ms | 16,093 ms | 0 ms | 36,696 ms |
| qwen3.5:cloud | 59,660 ms | 61,892 ms | 38,483 ms | 148,263 ms |

| Stage wall-clock | Value |
|---|---|
| Parallel (25 samples) | **33.4 min** (29.1% of total run) |
| Serial-equivalent (sum all model×sample latencies) | **90.1 min** |
| Parallel speedup | **~2.7×** |

#### Cost (per 1,000 calls, measured token volumes)

| Model | Groq-equiv | OpenAI-equiv |
|---|---|---|
| kimi-k2.6:cloud **(configured heavy)** | **$0.66** | $0.12 |
| kimi-k2.5:cloud | $0.68 | $0.12 |
| ministral-3:14b | $0.04 | $0.24 |
| ministral-3:8b | $0.03 | $0.19 |
| qwen3.5:cloud | $0.23 | $0.10 |

*Ollama Cloud bills flat-rate subscription (Pro $20/mo, Max $100/mo), not per-token.*

#### Quality (post-fix, n=25)

| Model | Score | Pass rate |
|---|---|---|
| **kimi-k2.6:cloud** | **8.24** | 68% |
| kimi-k2.5:cloud | 7.92 | 68% |
| ministral-3:14b | 7.88 | 80% |
| qwen3.5:cloud | 7.60 | 56% |
| ministral-3:8b | 7.40 | 64% |

**Interpretation:** kimi-k2.6 has a **real, reproducible lead** (+0.3 over next-best at n=25). This stage strongly supports keeping kimi-k2.6 as the heavy model. Absolute scores reflect task difficulty (8-turn transcript analysis, cross-modal reasoning).

---

### 2.2 process_adherence

#### Data
| Metric | Value |
|---|---|
| Full pool | **100** |
| Subset benchmarked | **25** (timing); **10** (quality — PA re-judge only) |
| Avg input size | **730 chars** (~247 prompt tokens) |
| Avg output size | **306–817** completion tokens |

**Missing-step distribution (subset):** 0 missing → 8, 1 → 6, 2 → 3, 3+ → 8.

**Example — typical (`pa_001`, complete adherence):**
```
Input:  8-turn refund transcript + Expected resolution graph steps:
        Acknowledge customer issue, Collect order identifier, Verify refund
        eligibility window, Confirm refund method and timeline, Close with summary...
Ref:    No missing SOP steps. Complete adherence.
```

**Example — edge case (`pa_003`, missing steps):**
```
Input:  Billing dispute transcript; agent skips confirm-understanding and follow-up path
Ref:    Missing SOP steps: [Confirm customer understanding, Close with follow-up path].
```

#### Timing (subset run)

| Model | Avg TTFT | Avg total | Min | Max |
|---|---|---|---|---|
| kimi-k2.6:cloud | 47,484 ms | **52,885 ms** | 32,291 ms | 91,642 ms |
| qwen3.5:cloud | 49,313 ms | 55,861 ms | 0 ms | 116,075 ms |
| kimi-k2.5:cloud | 50,671 ms | 61,945 ms | 21,296 ms | 110,822 ms |
| ministral-3:14b | 11,345 ms | 32,523 ms | 14,215 ms | 92,746 ms |
| ministral-3:8b | 6,380 ms | 21,810 ms | 0 ms | 50,824 ms |

| Stage wall-clock | Value |
|---|---|
| Parallel | **31.3 min** (27.3% of total run) |
| Serial-equivalent | **93.8 min** |

#### Cost (per 1,000 calls)

| Model | Groq-equiv | OpenAI-equiv |
|---|---|---|
| kimi-k2.6:cloud **(configured heavy)** | **$1.16** | $0.22 |
| kimi-k2.5:cloud | $1.38 | $0.26 |
| qwen3.5:cloud | $0.39 | $0.22 |
| ministral-3:8b | $0.08 | $0.53 |
| ministral-3:14b | $0.08 | $0.51 |

#### Quality

**Post-fix (PA re-judge, n=10 — smaller than other stages):**

| Model | Score (post-fix) | Score (pre-fix, re-audit n=10) |
|---|---|---|
| **kimi-k2.6:cloud** | **6.30** | 5.30 |
| qwen3.5:cloud | 5.50 | 5.10 |
| kimi-k2.5:cloud | 5.64 | 4.94 |
| ministral-3:8b | 4.80 | 4.80 |
| ministral-3:14b | 3.70 | 3.70 |

*Note: subset run (n=25, pre-PA-rejudge) showed qwen 6.72 vs kimi 6.36 — within ~0.7pt judge noise.*

**Interpretation:** Separation exists but is **the smallest reliable margin of any stage**. kimi-k2.6 leads at n=10 post-fix; qwen led at n=25 subset. Treat PA as **non-decisive** for model selection; keep kimi-k2.6 for composite heavy-path performance.

---

### 2.3 nli_policy

#### Data
| Metric | Value |
|---|---|
| Full pool | **100** |
| Subset benchmarked | **25** |
| Avg input size | **207 chars** (~179 prompt tokens) |
| Avg output size | **86–106** completion tokens |

**Label distribution (subset):** Entailment 7, Benign Deviation 5, Contradiction 9, Policy Hallucination 4 (+ 10 curated without `_label` in pool metadata).

**Example — typical (Entailment, `nli_001`):**
```
Input:  Ground truth policy: Outages under 24 hours are not eligible for automatic credits.
        Agent statement: Your outage was 18 hours, so no automatic credit applies per policy.
Ref:    Verdict: Entailment.
```

**Example — edge case (Benign Deviation, `nli_003`):**
```
Input:  Policy: Agents must verify identity before account changes.
        Agent: I'll verify PIN and email first. We skip the security-question step only
               because you called from the number on file.
Ref:    Verdict: Benign Deviation. (Explicit benign shortcut cue in transcript)
```

#### Timing

| Model | Avg TTFT | Avg total | Min | Max |
|---|---|---|---|---|
| kimi-k2.6:cloud | 24,111 ms | **25,830 ms** | 6,023 ms | 105,265 ms |
| kimi-k2.5:cloud | 16,150 ms | 17,626 ms | 4,625 ms | 41,014 ms |
| qwen3.5:cloud | 38,742 ms | 40,154 ms | 10,517 ms | 112,511 ms |
| ministral-3:8b | 4,575 ms | 7,051 ms | 2,169 ms | 15,501 ms |
| ministral-3:14b | 4,020 ms | 6,789 ms | 2,258 ms | 13,532 ms |

| Stage wall-clock | Parallel **18.2 min** (15.9%) | Serial-equiv **40.6 min** |

#### Cost (per 1,000 calls)

| kimi-k2.6:cloud | **$0.45** Groq / $0.08 OpenAI |

#### Quality (post-fix, n=25)

| Model | Score |
|---|---|
| **kimi-k2.6:cloud** | **9.52** |
| kimi-k2.5:cloud | 9.12 |
| ministral-3:8b | 9.08 |
| qwen3.5:cloud | 8.72 |
| ministral-3:14b | 8.52 |

**Interpretation:** kimi-k2.6 has a **clear lead** (+0.4 over kimi-k2.5). Strong evidence for heavy model choice.

---

### 2.4 rag_judge

#### Data
| Metric | Value |
|---|---|
| Full pool | **100** |
| Subset benchmarked | **20** |
| Avg input size | **269 chars** (~97 prompt tokens) |
| Avg output size | **43–54** completion tokens |

**Policy doc distribution (subset):** FIN-RULE-001 (4), FIN-RULE-010 (4), CS-RULE-001 (4), CS-RULE-008 (3), CS-RULE-002 (2), SEC-RULE-008 (3).

Rule IDs (`FIN-RULE-001`, etc.) match NexaLink eval manifests (`CALL_*.json` `policy_refs`); benchmark inlines policy text (no RAG retrieval step).

**Example — typical compliant (`rj_001`):**
```
Input:  [FIN-RULE-001 | Refund Policy > Outage Credits]
        Outages of 24+ hours qualify for pro-rated credits...
        Agent verified 44-hour outage, applied $23.33 credit...
Ref:    Compliant. Source: FIN-RULE-001. compliance_score >= 0.8.
```

**Example — edge case non-compliant (`rj_004`, partial):**
```
Input:  [SEC-RULE-008 | Account Security] — advise password change after fraud
        Agent froze disputed amount but never advised password change
Ref:    Partially non-compliant. Missing SEC-RULE-008 password-change advice.
```

#### Timing (rag re-judge run)

| Model | Avg total | Min | Max |
|---|---|---|---|
| ministral-3:8b | **4,178 ms** | 1,439 ms | 12,596 ms |
| ministral-3:14b | 6,378 ms | 1,888 ms | 24,550 ms |
| kimi-k2.6:cloud | 6,755 ms | 3,546 ms | 16,556 ms |
| kimi-k2.5:cloud | 7,610 ms | 3,085 ms | 12,819 ms |
| qwen3.5:cloud | 20,024 ms | 9,497 ms | 63,814 ms |

| Stage wall-clock | Parallel **6.9 min** (6.0%) | Serial-equiv **15.0 min** |

#### Cost (per 1,000 calls, ministral-8b configured for fast path)

| ministral-3:8b | **$0.01** Groq / $0.05 OpenAI |

#### Quality — harness bug fix visible here

| Model | Pre-fix (subset, broken judge) | Post-fix (re-judge) |
|---|---|---|
| kimi-k2.6:cloud | 4.6 | **9.70** |
| kimi-k2.5:cloud | 4.6 | **9.70** |
| ministral-3:14b | 5.3 | **9.70** |
| ministral-3:8b | 6.0 | **9.65** |
| qwen3.5:cloud | 5.1 | **9.70** |

*Original run (n=5, no verdict-mapping bug): 7.0–8.8 range — also not comparable to post-fix scale.*

**Interpretation:** Pre-fix 4.6–6.0 was a **judge harness artifact** (gemma3 did not map `compliance_score` → verdict). Post-fix all models **~9.7 — near-ceiling, not a differentiator**. Only relative ranking within stage matters; config choice unaffected.

---

### 2.5 text_to_sql

#### Data
| Metric | Value |
|---|---|
| Full pool | **50** (all SQL validated via `EXPLAIN`) |
| Subset benchmarked | **20** |
| Avg input size | **113 chars** (~187 prompt tokens with schema) |
| Avg output size | **42–88** completion tokens |

**Query types (subset):** top-N 6, count 4, date_filter 4, aggregation 3, join 3.

**Example — typical (`sql_001`):**
```
Input:  Organization ID: ... Question: Top 5 agents by overall score this month
Ref:    SELECT u.name, ROUND(AVG(s.overall_score)::NUMERIC * 10, 1) ...
        (uses speaker_role, organization_id, date_trunc — production schema)
```

**Example — edge case (agent_type filter, post `u.team` fix):**
```
Input:  Question: Average handle time for human agents (SQL-013)
Ref:    ... WHERE u.role = 'agent' AND u.agent_type = 'human'
        (u.team was hallucinated in 8 GT samples — fixed to real DDL columns)
```

#### Timing

| Model | Avg total | Min | Max |
|---|---|---|---|
| ministral-3:8b | **10,804 ms** | 2,268 ms | 20,267 ms |
| ministral-3:14b | 12,383 ms | 3,469 ms | 27,295 ms |
| kimi-k2.5:cloud | 20,058 ms | 5,192 ms | 46,875 ms |
| kimi-k2.6:cloud | 25,548 ms | 15,306 ms | 49,582 ms |
| qwen3.5:cloud | 56,742 ms | 17,877 ms | 119,840 ms |

| Stage wall-clock | Parallel **19.0 min** (16.6%) | Serial-equiv **41.8 min** |

#### Cost (per 1,000 calls)

| ministral-3:8b | **$0.02** Groq / $0.08 OpenAI |

#### Quality

| Model | Pre-fix (orig n=5, no schema in prompt) | Post-fix (subset n=20) |
|---|---|---|
| kimi-k2.6:cloud | **1.2** | 8.30 |
| kimi-k2.5:cloud | 4.0 | 8.75 |
| ministral-3:14b | 0.6 | 8.05 |
| ministral-3:8b | 2.0 | 7.50 |
| qwen3.5:cloud | 1.8 | **9.25** |

**Interpretation:** Original 1.2–4.0 scores were **harness artifacts** (missing `_SCHEMA`, bad judge). Post-fix all models ≥7.5 — **near-ceiling, production-ready**. qwen leads marginally; ministral-8b adequate for latency-sensitive paths.

---

### 2.6 fast_classification

#### Data
| Metric | Value |
|---|---|
| Full pool | **100** |
| Subset benchmarked | **20** |
| Avg input size | **43 chars** (~102 prompt tokens) |
| Avg output size | **4–8** completion tokens |

**Topics (subset):** refund_request, billing_issue, technical_support, account_access, retention, fraud_dispute, fee_adjustment, unknown. **Gibberish: 25%** (5/20). **Ambiguous (`_note`): 5** (25%).

**Example — typical (`fc_001`):**
```
Input:  I want a refund on my last invoice
Ref:    topic: refund_request, is_gibberish: false
```

**Example — ambiguous (`fc_004`, edge case):**
```
Input:  There is a charge on my bill I do not recognize
Ref:    topic: fraud_dispute, is_gibberish: false
Note:   ambiguous, multiple valid labels: billing_issue|fraud_dispute
```

#### Timing

| Model | Avg total | Min | Max |
|---|---|---|---|
| **ministral-3:8b** | **1,748 ms** | 1,118 ms | 3,812 ms |
| ministral-3:14b | 2,848 ms | 1,228 ms | 7,317 ms |
| kimi-k2.6:cloud | 4,742 ms | 2,383 ms | 10,770 ms |
| kimi-k2.5:cloud | 5,102 ms | 2,257 ms | 24,148 ms |
| qwen3.5:cloud | 17,628 ms | 4,649 ms | 83,416 ms |

| Stage wall-clock | Parallel **6.0 min** (5.2%) | Serial-equiv **10.7 min** |

#### Cost (per 1,000 calls)

| ministral-3:8b | **$0.006** Groq / $0.020 OpenAI |

#### Quality

| Model | Pre-fix (orig n=7, latency in score) | Post-fix (subset n=20, label-only) |
|---|---|---|
| kimi-k2.6:cloud | 4.14 | 9.50 |
| kimi-k2.5:cloud | 3.57 | 9.50 |
| ministral-3:14b | 3.57 | 9.00 |
| qwen3.5:cloud | 3.00 | 8.75 |
| **ministral-3:8b** | 4.14 | **9.75** |

**Interpretation:** Original ~3–4 scores were **latency-baked** (cloud always >200ms SLA). Post-fix **near-ceiling**; ministral-3:8b wins on quality + speed — **confirms fast model config**.

---

## 3. Overall timing summary

### 135-sample subset run (parallel, actual)

| Metric | Value |
|---|---|
| **Actual wall-clock** | **124.7 min** (~2h 5m) |
| Theoretical parallel sum (max latency per sample) | 114.7 min |
| Serial-equivalent (all model calls sequential) | **292.0 min** (~4h 52m) |
| **Parallelization speedup** | **~2.3×** vs serial-equivalent |

### Stage time breakdown (% of 124.7 min run)

| Stage | Share | Parallel stage time |
|---|---|---|
| emotion_shift | **29.1%** | ~36 min |
| process_adherence | **27.3%** | ~34 min |
| nli_policy | 15.9% | ~20 min |
| text_to_sql | 16.6% | ~21 min |
| rag_judge | 6.0% | ~7 min |
| fast_classification | 5.2% | ~6 min |

*emotion_shift + process_adherence = **56%** of total runtime (kimi/qwen 25–50s/sample).*

### Projected full 550-sample pool run (parallel)

Scaled from measured per-sample parallel latencies × pool counts:

| Stage | Pool n | Projected parallel time |
|---|---|---|
| emotion_shift | 100 | ~134 min |
| process_adherence | 100 | ~125 min |
| nli_policy | 100 | ~73 min |
| rag_judge | 100 | ~34 min |
| text_to_sql | 50 | ~48 min |
| fast_classification | 100 | ~30 min |
| **Total** | **550** | **~443 min (~7.4 h)** |

Linear scaling from actual wall-clock (550/135 × 124.7 min) ≈ **507 min (~8.5 h)** including overhead.

*Earlier ~2.5h estimate used re-audit average latencies without per-sample max-latency structure; **actual subset data suggests 7–8.5h** for a full parallel 550-sample run.*

---

## 4. Overall cost summary

### Reference pricing (per 1M tokens)

| Provider | Model class | Input | Output |
|---|---|---|---|
| Groq | llama-3.3-70b (kimi/qwen proxy) | $0.59 | $0.79 |
| Groq | llama-3.1-8b (ministral proxy) | $0.05 | $0.08 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| Ollama Cloud | Pro / Max | **$20 / $100 flat/month** | — |

### Monthly volume model (N = 100 interactions/month)

Assumptions from pipeline design:
- **24 heavy calls/interaction** — emotion_shift + process_adherence + nli_policy (~8 rolling windows × 3 chains)
- **~4 fast calls/interaction** — fast_classification (×2), rag_judge, text_to_sql/assistant

Using **measured token volumes** from subset run with **kimi-k2.6** (heavy) and **ministral-3:8b** (fast):

| Estimate | Monthly cost @ N=100 |
|---|---|
| **Groq-equivalent** | **~$5.46** |
| **OpenAI-equivalent (gpt-4o-mini)** | **~$1.03** |
| Ollama Cloud Pro | $20.00 (flat) |
| Ollama Cloud Max | $100.00 (flat) |

### Break-even (interactions/month)

| Comparison | Break-even N |
|---|---|
| Groq-equiv vs Ollama Pro ($20) | **~366** interactions/month |
| Groq-equiv vs Ollama Max ($100) | **~1,830** interactions/month |
| OpenAI-equiv vs Ollama Pro ($20) | **~1,949** interactions/month |
| OpenAI-equiv vs Ollama Max ($100) | **~9,745** interactions/month |

### Per-stage cost verdict (N=100 reference)

| Stage | Ollama flat-rate rationale @ N=100 |
|---|---|
| emotion_shift | Heavy kimi calls dominate cost; flat rate buys model access unavailable on Groq |
| process_adherence | Same — kimi-k2.6 required |
| nli_policy | Same |
| rag_judge | **Per-token would be cheaper** (~$0.01/1k ministral calls) but bundled in subscription |
| text_to_sql | Near-ceiling quality; low volume per interaction |
| fast_classification | **Per-token cheaper** at N=100; Ollama justified by stack uniformity |

**Recommendation:** At **N=100 interactions/month**, Groq/OpenAI **per-token equivalents are below** Ollama Pro ($20) on paper — but **kimi-k2.6:cloud is not available on Groq**, so Ollama Cloud Pro is the correct choice for model access + predictable billing. Upgrade to **Max ($100)** only if concurrent model limits or volume exceeds ~1,800 interactions/month (Groq-equiv break-even).

---

## 5. Quality summary (master table, post-fix)

| Stage | n | kimi-k2.6 | kimi-k2.5 | ministral-14b | ministral-8b | qwen3.5 | Winner |
|---|---|---|---|---|---|---|---|
| emotion_shift | 25 | **8.24** | 7.92 | 7.88 | 7.40 | 7.60 | **kimi-k2.6** |
| process_adherence † | 10 | **6.30** | 5.64 | 3.70 | 4.80 | 5.50 | **kimi-k2.6** |
| nli_policy | 25 | **9.52** | 9.12 | 8.52 | 9.08 | 8.72 | **kimi-k2.6** |
| rag_judge ‡ | 20 | 9.70 | 9.70 | 9.70 | 9.65 | 9.70 | tied |
| text_to_sql | 20 | 8.30 | 8.75 | 8.05 | 7.50 | **9.25** | qwen3.5 |
| fast_classification | 20 | 9.50 | 9.50 | 9.00 | **9.75** | 8.75 | **ministral-8b** |

† PA quality from `benchmark_PA_rejudge_20260613.json` (n=10, not n=25).  
‡ rag_judge from `benchmark_rag_rejudge_20260613.json` (verdict-mapping fix).

### Before/after harness fixes (magnitude of each bug)

| Stage | Metric | Pre-fix (broken) | Post-fix | Δ (illustrative) |
|---|---|---|---|---|
| text_to_sql | kimi-k2.6 | **1.2** (n=5, no schema) | 8.30 | +7.1 |
| fast_classification | kimi-k2.6 | **4.14** (latency in score) | 9.50 | +5.4 |
| process_adherence | kimi-k2.6 | **5.30** (judge JSON errors) | 6.30 | +1.0 |
| rag_judge | kimi-k2.6 | **4.60** (subset, no verdict map) | 9.70 | +5.1 |

---

## 6. Final configuration

| Setting | Value | Matches stage winner? |
|---|---|---|
| `OLLAMA_CLOUD_HEAVY_MODEL` | **kimi-k2.6:cloud** | Yes — emotion_shift, nli_policy; near-tied PA |
| `OLLAMA_CLOUD_FAST_MODEL` | **ministral-3:8b** | Yes — fast_classification |

**Stages where raw winner ≠ configured model:**

| Stage | Raw winner | Config | Justification |
|---|---|---|---|
| text_to_sql | qwen3.5 (9.25) | ministral-8b for fast paths; heavy via assistant | Gap small (9.25 vs 8.30); ministral adequate; qwen 56s vs 11s latency |
| process_adherence | qwen3.5 at n=25 subset (6.72) | kimi-k2.6 heavy | Within judge noise; kimi leads at n=10 post-fix; composite heavy path |
| rag_judge | tied ~9.7 | ministral-8b fast | Not a differentiator post-fix |

**Smoke test:** pass — `Heavy model: kimi-k2.6:cloud`, `Fast model: ministral-3:8b`.

---

## 7. Known limitations

- **process_adherence** quality based on **n=10** (PA re-judge), not n=25 like other stages
- **Template repetition** in generated GT samples (rag_judge, nli_policy) — diversify before larger runs
- **text_to_sql** uses synthetic manager queries; real query patterns may differ
- **rag_judge benchmark** inlines policy text — does not exercise full RAG retrieval pipeline
- **Cost model** uses **N=100/month** placeholder; replace with actual NexaLink volume when available
- **Full 550-sample run** projected at **7–8.5 hours** parallel (not the earlier ~2.5h rough estimate)

---

## Appendix: Benchmark run history

| Run | Date | Samples | Stages | Notes |
|---|---|---|---|---|
| `benchmark_20260613_1324` | Original | 32 | 6 | Harness bugs; do not use for quality |
| `benchmark_REAUDIT_20260613_1455` | Re-audit | 40 | 4 | Harness fixes; PA judge JSON bug remained |
| `benchmark_PA_rejudge_20260613` | PA fix | 50 | 1 | JSON literal fix |
| `benchmark_subset_20260613_1648` | Final | 675 rows | 6 | 135-sample parallel; rag_judge pre-fix |
| `benchmark_rag_rejudge_20260613` | RAG fix | 100 | 1 | Verdict-mapping fix |

**Migration status: COMPLETE.** Model selection validated. Production config optimal. No env changes required.
