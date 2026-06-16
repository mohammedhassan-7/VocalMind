# VocalMind Ollama Cloud Model Benchmark Summary

Source: `benchmark_20260613_1324.json`
Generated: 2026-06-13T11:19:03.861407+00:00

**Judge:** `ministral-3:8b` via Ollama Cloud (OPENAI_API_KEY not set; gpt-4o-mini unavailable).

## D.1 — Per-stage results

### Stage: emotion_shift

| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |
|---|---|---|---|---|---|---|---|
| kimi-k2.5:cloud | 10.0 | 100% | 25347 | 28132 | $0.69 | $0.13 | EXCEEDS 3000ms |
| ministral-3:14b | 10.0 | 100% | 868 | 7373 | $0.03 | $0.18 | EXCEEDS 3000ms |
| ministral-3:8b | 10.0 | 100% | 876 | 4399 | $0.02 | $0.11 | EXCEEDS 3000ms |
| qwen3.5:cloud | 9.4 | 100% | 40961 | 42492 | $0.18 | $0.08 | EXCEEDS 3000ms |
| kimi-k2.6:cloud | 8.8 | 100% | 24791 | 26675 | $0.58 | $0.11 | EXCEEDS 3000ms |

### Stage: process_adherence

| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |
|---|---|---|---|---|---|---|---|
| kimi-k2.5:cloud | 8.8 | 80% | 17523 | 26895 | $1.37 | $0.26 | EXCEEDS 3000ms |
| qwen3.5:cloud | 7.0 | 40% | 38740 | 43832 | $0.33 | $0.19 | EXCEEDS 3000ms |
| ministral-3:8b | 5.6 | 40% | 883 | 17752 | $0.07 | $0.47 | EXCEEDS 3000ms |
| ministral-3:14b | 4.8 | 40% | 843 | 15720 | $0.07 | $0.52 | EXCEEDS 3000ms |
| kimi-k2.6:cloud | 4.2 | 40% | 28230 | 32748 | $1.23 | $0.24 | EXCEEDS 3000ms |

### Stage: nli_policy

| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |
|---|---|---|---|---|---|---|---|
| ministral-3:14b | 8.0 | 80% | 764 | 2839 | $0.02 | $0.08 |  |
| ministral-3:8b | 8.0 | 80% | 778 | 2787 | $0.02 | $0.09 |  |
| kimi-k2.5:cloud | 7.4 | 80% | 12761 | 15466 | $0.46 | $0.08 | EXCEEDS 3000ms |
| kimi-k2.6:cloud | 6.6 | 60% | 15191 | 16596 | $0.44 | $0.08 | EXCEEDS 3000ms |
| qwen3.5:cloud | 6.0 | 60% | 29882 | 31347 | $0.17 | $0.08 | EXCEEDS 3000ms |

### Stage: rag_judge

| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |
|---|---|---|---|---|---|---|---|
| ministral-3:8b | 8.8 | 80% | 847 | 2234 | $0.01 | $0.05 |  |
| kimi-k2.6:cloud | 8.2 | 60% | 5075 | 6015 | $0.28 | $0.05 | EXCEEDS 5000ms |
| ministral-3:14b | 8.2 | 60% | 765 | 2157 | $0.01 | $0.05 |  |
| kimi-k2.5:cloud | 7.4 | 60% | 7611 | 8983 | $0.28 | $0.05 | EXCEEDS 5000ms |
| qwen3.5:cloud | 7.0 | 60% | 17909 | 19014 | $0.09 | $0.04 | EXCEEDS 5000ms |

### Stage: text_to_sql

| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |
|---|---|---|---|---|---|---|---|
| kimi-k2.5:cloud | 4.0 | 40% | 64040 | 65436 | $0.24 | $0.04 | EXCEEDS 2000ms |
| ministral-3:8b | 2.0 | 20% | 884 | 3260 | $0.01 | $0.06 | EXCEEDS 2000ms |
| qwen3.5:cloud | 1.8 | 0% | 68131 | 69475 | $0.11 | $0.04 | EXCEEDS 2000ms |
| kimi-k2.6:cloud | 1.2 | 0% | 44549 | 45548 | $0.24 | $0.04 | EXCEEDS 2000ms |
| ministral-3:14b | 0.6 | 0% | 848 | 3011 | $0.01 | $0.06 | EXCEEDS 2000ms |

### Stage: fast_classification

| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |
|---|---|---|---|---|---|---|---|
| kimi-k2.6:cloud | 4.1 | 29% | 2732 | 2993 | $0.11 | $0.02 | EXCEEDS 200ms |
| ministral-3:8b | 4.1 | 29% | 879 | 1285 | $0.01 | $0.02 | EXCEEDS 200ms |
| kimi-k2.5:cloud | 3.6 | 14% | 5730 | 6011 | $0.11 | $0.02 | EXCEEDS 200ms |
| ministral-3:14b | 3.6 | 14% | 756 | 1180 | $0.01 | $0.02 | EXCEEDS 200ms |
| qwen3.5:cloud | 3.0 | 0% | 27899 | 28294 | $0.06 | $0.02 | EXCEEDS 200ms |

## D.2 — Cost summary

### Monthly Cost Estimate (N=100 interactions/month)

Assumptions: 24 heavy calls + 5 fast calls per interaction; token counts from ground-truth averages.

| Provider | Monthly cost | Notes |
|---|---|---|
| Ollama Cloud Pro | $20 flat | 3 concurrent models |
| Groq equivalent (heavy=llama-3.3-70b, fast=llama-3.1-8b) | $0.91 | per-token estimate |
| OpenAI equivalent (gpt-4o-mini for all) | $0.56 | per-token estimate |

**Break-even:** Ollama Cloud Pro is cheaper than Groq when monthly interactions > **2192**

## D.3 — Recommendation

### Model Recommendation

**Heavy stages** (emotion_shift, process_adherence, nli_policy):
- Current: `kimi-k2.6:cloud`
- **Replace with `kimi-k2.5:cloud`**
- Average score across heavy stages: **8.7/10**; emotion_shift latency 28132ms
- Rationale: `kimi-k2.5:cloud` leads on process_adherence (8.8/10) while matching top emotion_shift scores; `kimi-k2.6:cloud` trails on process_adherence (4.2/10).

**Fast stages** (fast_classification, rag_judge):
- Current: `ministral-3:8b`
- **Confirmed**
- Combined fast avg score: **6.5/10** (rag_judge 8.8/10 leader)

**Text-to-SQL** (assistant):
- Current: `ministral-3:8b`
- **Keep `ministral-3:8b` for latency** (best balance); all models scored ≤4/10 on SQL (judge via ministral-3:8b). Top SQL scorer: `kimi-k2.5:cloud` at 4.0/10 but 65s latency.

Update env vars:
```dotenv
OLLAMA_CLOUD_HEAVY_MODEL=kimi-k2.5:cloud
OLLAMA_CLOUD_FAST_MODEL=ministral-3:8b
```
