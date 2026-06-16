## VocalMind Ollama Cloud Model Benchmark — 2026-06-13 12:37 UTC

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
| kimi-k2.6:cloud | 5.3 | 10% | 25875ms | 30666ms | $1.09 | $0.21 |
| qwen3.5:cloud | 5.1 | 10% | 33506ms | 38422ms | $0.30 | $0.17 |
| kimi-k2.5:cloud | 4.9 | 10% | 24655ms | 34015ms | $1.18 | $0.23 |
| ministral-3:8b | 4.8 | 0% | 876ms | 18796ms | $0.08 | $0.52 |
| ministral-3:14b | 3.7 | 10% | 1107ms | 16036ms | $0.07 | $0.50 |

### Stage: nli_policy
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| kimi-k2.5:cloud | 10.0 | 100% | 11794ms | 14335ms | $0.47 | $0.09 |
| qwen3.5:cloud | 10.0 | 100% | 29830ms | 31349ms | $0.18 | $0.08 |
| kimi-k2.6:cloud | 9.7 | 100% | 15644ms | 16942ms | $0.44 | $0.08 |
| ministral-3:14b | 9.7 | 90% | 777ms | 2613ms | $0.02 | $0.08 |
| ministral-3:8b | 9.3 | 90% | 1231ms | 3387ms | $0.02 | $0.09 |

### Stage: rag_judge
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: text_to_sql
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| kimi-k2.6:cloud | 8.8 | 60% | 18067ms | 19307ms | $0.34 | $0.06 |
| kimi-k2.5:cloud | 8.8 | 60% | 24225ms | 26050ms | $0.33 | $0.06 |
| ministral-3:8b | 8.8 | 60% | 764ms | 3010ms | $0.02 | $0.09 |
| ministral-3:14b | 8.2 | 40% | 1004ms | 3731ms | $0.02 | $0.08 |
| qwen3.5:cloud | 8.2 | 40% | 71120ms | 72512ms | $0.15 | $0.06 |

### Stage: fast_classification
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| kimi-k2.6:cloud | 10.0 | 100% | 3021ms | 3298ms | $0.11 | $0.02 |
| kimi-k2.5:cloud | 10.0 | 100% | 4662ms | 4999ms | $0.11 | $0.02 |
| ministral-3:14b | 10.0 | 100% | 852ms | 1280ms | $0.01 | $0.02 |
| ministral-3:8b | 10.0 | 100% | 943ms | 1394ms | $0.01 | $0.02 |
| qwen3.5:cloud | 9.3 | 86% | 18605ms | 19117ms | $0.06 | $0.02 |

### Recommendation
Paste this section manually after reviewing results:
- Heavy stages (emotion_shift, process_adherence, nli_policy): use ___________
- Fast stages (fast_classification): use ___________
- RAG judge: use ___________
- Embeddings: use ___________

Total benchmark rows: 160