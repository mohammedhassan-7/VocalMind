## VocalMind Ollama Cloud Model Benchmark — 2026-06-14 10:57 UTC

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
| ministral-3:14b | 7.3 | 78% | 1154ms | 13396ms | $0.05 | $0.32 |
| kimi-k2.5:cloud | 6.6 | 39% | 19966ms | 21628ms | $0.54 | $0.10 |
| kimi-k2.6:cloud | 5.8 | 38% | 26975ms | 28164ms | $0.50 | $0.09 |

### Stage: process_adherence
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: nli_policy
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

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

Total benchmark rows: 510