## VocalMind Ollama Cloud Model Benchmark — 2026-06-16 12:42 UTC

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
| gpt-oss:20b | 0.0 | 0% | 74888ms | 76212ms | $0.04 | $0.11 |
| deepseek-v3.1:671b | 0.0 | 0% | 72560ms | 94271ms | $0.48 | $0.15 |
| qwen3.5:cloud | 0.0 | 0% | 121292ms | 124087ms | $0.49 | $0.15 |
| gemma3:12b | 0.0 | 0% | 54235ms | 59626ms | $0.04 | $0.15 |
| kimi-k2.5:cloud | 0.0 | 0% | 85960ms | 87960ms | $0.88 | $0.14 |
| kimi-k2.6:cloud | 0.0 | 0% | 83119ms | 84280ms | $0.84 | $0.13 |
| ministral-3:14b | 0.0 | 0% | 61482ms | 64423ms | $0.05 | $0.18 |
| ministral-3:8b | 0.0 | 0% | 66674ms | 69630ms | $0.05 | $0.18 |

### Stage: process_adherence
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|

### Stage: nli_policy
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| gpt-oss:20b | 0.0 | 0% | 78724ms | 80226ms | $0.03 | $0.09 |
| kimi-k2.6:cloud | 0.0 | 0% | 81772ms | 82961ms | $0.71 | $0.12 |
| gemma3:12b | 0.0 | 0% | 66186ms | 69391ms | $0.03 | $0.10 |
| ministral-3:14b | 0.0 | 0% | 80921ms | 82614ms | $0.03 | $0.12 |
| ministral-3:8b | 0.0 | 0% | 82985ms | 84666ms | $0.04 | $0.14 |
| deepseek-v3.1:671b | 0.0 | 0% | 73896ms | 83246ms | $0.32 | $0.10 |
| kimi-k2.5:cloud | 0.0 | 0% | 86711ms | 88195ms | $0.78 | $0.13 |
| qwen3.5:cloud | 0.0 | 0% | 121634ms | 124106ms | $0.47 | $0.15 |

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

Total benchmark rows: 2736