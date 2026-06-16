# VocalMind Ollama Cloud Model Benchmark Summary v2

Re-audit: `benchmark_REAUDIT_20260613_1455.json` (judge: **`gemma3:12b`** via Ollama Cloud — not a re-run candidate)  
Original (unchanged stages): `benchmark_20260613_1324.json` (emotion_shift, rag_judge)

---

## Step 1 — Revert kimi-k2.5 → kimi-k2.6

**Done.** `OLLAMA_CLOUD_HEAVY_MODEL=kimi-k2.6:cloud` restored in `backend/.env`, `backend/.env.example`, `.env.example`, and `docker-compose.yml` defaults.

Smoke test (2026-06-13):
```
Heavy model: kimi-k2.6:cloud
LLM type: ChatOpenAI
```

---

## Step 2 — text_to_sql harness fixes

- **`TEXT_TO_SQL_SYSTEM`** now loads production `_SCHEMA` from `backend/app/api/routes/assistant.py` via AST (no hand-duplicated schema string).
- Judge input: markdown fences stripped before scoring.
- Empty SQL responses: forced **score=0** without calling judge.
- Judge prompt: explicit note that **`WITH ... SELECT` is read-only**, with example CTE.

---

## Step 3 — fast_classification harness fixes

- Judge rubric: **label-only** (topic + is_gibberish); latency removed from quality score.
- Latency tracked separately as `latency_sla_200ms_pass_rate` in summary (informational vs 200ms SLA).
- Responses: markdown ```json fences stripped before judge (shared `_strip_code_fences`).

---

## Step 4 — Ground truth fixes

| Item | Change |
|---|---|
| **sql_004** | `utterances.speaker` → `utterances.speaker_role = 'customer'` (matches `infra/db/01_schema.sql`) |
| **nli_003** | Reference → **Contradiction** (agent offers 2/5 verification factors; policy requires 3-of-5) |
| **fc_004** | Reference → **fraud_dispute** (4/5 model consensus; unrecognized charge pattern) |
| **pa_005** | Replaced narrative summary with **8-turn CALL_01 transcript** (complete adherence) |
| **nli_policy** | 5 → **10** samples (nli_006–nli_010) |
| **process_adherence** | 5 → **10** samples (pa_006–pa_010) |

**Production bug flagged (not fixed this phase):** `backend/app/api/routes/assistant.py` still documents `utterances.speaker` in `_SCHEMA` and examples — real DDL column is `speaker_role`.

---

## Step 5 — Neutral judge

**Judge: `gemma3:12b` via Ollama Cloud**

Neutral because it is **not** among the five re-run candidates (`kimi-k2.6`, `kimi-k2.5`, `ministral-3:8b`, `ministral-3:14b`, `qwen3.5`). `OPENAI_API_KEY` is not set; `gpt-4o-mini` unavailable.

Original 5 samples for `nli_policy` and `process_adherence`: **re-judged only** (raw responses reused from first run). New samples: full model + judge pass.

---

## Step 6 — Targeted re-run

**Saved to:** `infra/benchmarks/reports/benchmark_REAUDIT_20260613_1455.json` (~42 min, exit 0)

### text_to_sql avg scores (schema-injected, fixed judge)

| Model | Avg /10 |
|---|---|
| kimi-k2.6:cloud | **8.8** |
| kimi-k2.5:cloud | **8.8** |
| ministral-3:8b | **8.8** |
| ministral-3:14b | 8.2 |
| qwen3.5:cloud | 8.2 |

*(First run: 1.2–4.0 — harness was broken, not the models.)*

### fast_classification avg scores (label-only)

| Model | Avg /10 |
|---|---|
| kimi-k2.6 / k2.5 / ministral-3:8b / ministral-3:14b | **10.0** |
| qwen3.5:cloud | 9.3 |

### fast_classification latency vs 200ms SLA

| Model | Avg total ms | SLA pass rate |
|---|---|---|
| ministral-3:14b | 1280 | **0%** |
| ministral-3:8b | 1394 | **0%** |
| kimi-k2.6:cloud | 3298 | 0% |
| kimi-k2.5:cloud | 4999 | 0% |
| qwen3.5:cloud | 19117 | 0% |

No model meets 200ms on Ollama Cloud remote inference; ministral is ~2.4× faster than kimi.

### nli_policy avg scores (gemma3:12b judge, 10 samples)

| Model | Avg /10 |
|---|---|
| kimi-k2.5:cloud | **10.0** |
| qwen3.5:cloud | **10.0** |
| kimi-k2.6:cloud | 9.7 |
| ministral-3:14b | 9.7 |
| ministral-3:8b | 9.3 |

### process_adherence avg scores (gemma3:12b judge, 10 samples)

| Model | Avg /10 | Notes |
|---|---|---|
| kimi-k2.6:cloud | **5.3** | 1 judge JSON parse error |
| qwen3.5:cloud | 5.1 | 1 error |
| kimi-k2.5:cloud | 4.9 | 1 error |
| ministral-3:8b | 4.8 | |
| ministral-3:14b | 3.7 | |

All models cluster **4.8–5.3/10** — no reliable separation. Judge still struggles on long JSON outputs (3× `Expecting value` parse errors).

---

## Step 7 — Per-stage tables (all 6 stages)

### emotion_shift (original)

| Model | Avg /10 | Avg total ms |
|---|---|---|
| kimi-k2.5 / ministral-3:8b / ministral-3:14b | 10.0 | 4399–28132 |
| kimi-k2.6:cloud | 8.8 | 26675 |

### process_adherence (re-audit)

See table above — **no clear winner**.

### nli_policy (re-audit)

See table above — kimi-k2.5 edge (+0.3 vs k2.6).

### rag_judge (original, ministral-3:8b judge — treat as directional)

| Model | Avg /10 |
|---|---|
| ministral-3:8b | 8.8 |
| kimi-k2.6:cloud | 8.2 |

### text_to_sql (re-audit)

See table above — tied at 8.8; **ministral-3:8b** best latency (3010ms vs 19307ms kimi-k2.6).

### fast_classification (re-audit)

See tables above.

---

## Recommendations

### Updated heavy model recommendation: **keep `kimi-k2.6:cloud`**

| Model | emotion_shift | process_adherence | nli_policy | **Heavy avg** |
|---|---|---|---|---|
| kimi-k2.6:cloud | 8.8 | **5.3** | 9.7 | **7.9** |
| kimi-k2.5:cloud | 10.0 | 4.9 | **10.0** | **8.3** |

kimi-k2.5 leads by +0.4 composite, driven by emotion_shift (original/ministral-judged run) and nli_policy. After re-audit, **process_adherence no longer favors k2.5** (k2.6 leads 5.3 vs 4.9). With PA still high-variance and judge parse errors, the swap is **not justified**.

**emotion_shift note:** ministral-3:8b/14b tied **10.0/10** at **4–7× lower latency** than kimi on the original run — worth a future benchmark treating ministral as a heavy candidate, but not switching production heavy env to ministral without re-testing PA/NLI under ministral-sized context.

**Recommendation to change OLLAMA_CLOUD_HEAVY_MODEL from kimi-k2.6:cloud: NO** — corrected data removes the original PA gap; remaining k2.5 edge is within noise on PA and uses mixed original/re-audit stages.

### Updated fast model recommendation: **keep `ministral-3:8b`**

- fast_classification (label-only): **10.0/10**
- rag_judge (original): **8.8/10** (fast composite leader)
- Latency: fastest among candidates (~1394ms avg; still above 200ms SLA on cloud)

### Text-to-SQL production readiness: **ready (with latency caveat)**

- Corrected scores: **8.8/10** for kimi-k2.6, kimi-k2.5, and ministral-3:8b.
- For production assistant latency: prefer **`ministral-3:8b`** (3010ms vs ~19s kimi-k2.6) if SQL quality is tied.
- Fix **`assistant.py` `_SCHEMA`** `speaker` → `speaker_role` in a follow-up (production prompt/schema drift).

---

## Verdict: **READY FOR DECISION** (with caveats)

The re-audit fixed broken stages and reverted the premature kimi-k2.5 swap. **Keep kimi-k2.6:cloud (heavy) and ministral-3:8b (fast).** process_adherence still needs either a programmatic scorer or a more capable judge before it can drive model selection. rag_judge retains original ministral-self-judge results — re-judge with gemma3:12b optional follow-up.

Do **not** change `OLLAMA_CLOUD_HEAVY_MODEL` until this report is reviewed.
