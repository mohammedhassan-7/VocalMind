## VocalMind Ollama Cloud Model Benchmark — 2026-06-15 15:44 UTC

### Cost methodology
Ollama Cloud does not publish per-token prices — it bills on GPU time consumed,
which depends on model size (usage level 1–4) and request duration.
We therefore show two cost columns:
  - groq_equivalent_usd: what the same token volume would cost on Groq for the
    nearest equivalent model family. Use this to sanity-check token efficiency.
  - openai_equivalent_usd: same calculation against gpt-4o-mini as a market anchor.
To convert to Ollama Cloud subscription cost: divide your Pro/Max plan monthly fee
by your estimated monthly call count. VocalMind's 3-chain trigger runs ~24 LLM
calls per interaction (3 chains × ~8 windows). At 500 interactions/month that is
~12,000 calls/month → $0.0017/call on Pro, $0.0083/call on Max.

### Stage: emotion_shift
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: process_adherence
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: nli_policy
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| deepseek-v3.1:671b | 0.0 | 0% | 5250ms | 23126ms | $0.56 | $0.18 |
| gemma3:12b | 0.0 | 0% | 1318ms | 10511ms | $0.05 | $0.18 |
| gpt-oss:20b | 0.0 | 0% | 18443ms | 18443ms | $0.04 | $0.13 |
| kimi-k2.5:cloud | 0.0 | 0% | 27105ms | 29221ms | $1.10 | $0.18 |
| kimi-k2.6:cloud | 0.0 | 0% | 9992ms | 11012ms | $1.05 | $0.17 |
| ministral-3:14b | 0.0 | 0% | 1327ms | 3448ms | $0.05 | $0.19 |
| ministral-3:8b | 0.0 | 0% | 877ms | 3534ms | $0.05 | $0.19 |
| qwen3.5:cloud | 0.0 | 0% | 77150ms | 88637ms | $0.57 | $0.19 |

### Stage: rag_judge
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: text_to_sql
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: fast_classification
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Recommendation
Paste this section manually after reviewing results:
- Heavy stages (emotion_shift, process_adherence, nli_policy): use ___________
- Fast stages (fast_classification): use ___________
- RAG judge: use ___________
- Embeddings: use ___________

Total benchmark rows: 8