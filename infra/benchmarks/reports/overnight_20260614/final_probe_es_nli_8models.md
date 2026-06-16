## VocalMind Ollama Cloud Model Benchmark — 2026-06-15 15:49 UTC

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
| gemma3:12b | 0.0 | 0% | 9102ms | 14188ms | $0.04 | $0.13 |
| kimi-k2.5:cloud | 0.0 | 0% | 20722ms | 21915ms | $0.89 | $0.14 |
| kimi-k2.6:cloud | 0.0 | 0% | 16181ms | 17277ms | $0.87 | $0.14 |
| ministral-3:14b | 0.0 | 0% | 6940ms | 9298ms | $0.04 | $0.17 |
| deepseek-v3.1:671b | 0.0 | 0% | 3204ms | 25071ms | $0.45 | $0.15 |
| ministral-3:8b | 0.0 | 0% | 14115ms | 17614ms | $0.04 | $0.16 |
| gpt-oss:20b | 0.0 | 0% | 18404ms | 18404ms | $0.03 | $0.10 |
| qwen3.5:cloud | 0.0 | 0% | 64413ms | 68289ms | $0.45 | $0.15 |

### Stage: process_adherence
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: nli_policy
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| gemma3:12b | 0.0 | 0% | 5150ms | 10008ms | $0.05 | $0.16 |
| gpt-oss:20b | 0.0 | 0% | 14936ms | 14936ms | $0.04 | $0.13 |
| kimi-k2.5:cloud | 0.0 | 0% | 16503ms | 18260ms | $1.12 | $0.18 |
| kimi-k2.6:cloud | 0.0 | 0% | 16127ms | 17409ms | $1.12 | $0.18 |
| ministral-3:14b | 0.0 | 0% | 20929ms | 23004ms | $0.05 | $0.18 |
| ministral-3:8b | 0.0 | 0% | 21967ms | 24519ms | $0.05 | $0.18 |
| deepseek-v3.1:671b | 0.0 | 0% | 12438ms | 32914ms | $0.57 | $0.18 |
| qwen3.5:cloud | 0.0 | 0% | 72521ms | 74722ms | $0.56 | $0.18 |

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

Total benchmark rows: 64