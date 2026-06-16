## VocalMind Ollama Cloud Model Benchmark — 2026-06-13 15:53 UTC

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
| kimi-k2.6:cloud | 8.2 | 68% | 46680ms | 48975ms | $0.66 | $0.12 |
| kimi-k2.5:cloud | 7.9 | 68% | 65917ms | 72194ms | $0.68 | $0.12 |
| ministral-3:14b | 7.9 | 80% | 9149ms | 17080ms | $0.04 | $0.24 |
| qwen3.5:cloud | 7.6 | 56% | 59660ms | 61892ms | $0.23 | $0.10 |
| ministral-3:8b | 7.4 | 64% | 9648ms | 16093ms | $0.03 | $0.19 |

### Stage: process_adherence
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| qwen3.5:cloud | 6.7 | 20% | 49313ms | 55861ms | $0.39 | $0.22 |
| kimi-k2.6:cloud | 6.4 | 20% | 47484ms | 52885ms | $1.16 | $0.22 |
| kimi-k2.5:cloud | 5.9 | 16% | 50671ms | 61945ms | $1.38 | $0.26 |
| ministral-3:8b | 4.7 | 4% | 6380ms | 21810ms | $0.08 | $0.53 |
| ministral-3:14b | 4.1 | 0% | 11345ms | 32523ms | $0.08 | $0.51 |

### Stage: nli_policy
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| kimi-k2.6:cloud | 9.5 | 92% | 24111ms | 25830ms | $0.45 | $0.08 |
| kimi-k2.5:cloud | 9.1 | 92% | 16150ms | 17626ms | $0.46 | $0.08 |
| ministral-3:8b | 9.1 | 80% | 4575ms | 7051ms | $0.02 | $0.09 |
| qwen3.5:cloud | 8.7 | 72% | 38742ms | 40154ms | $0.18 | $0.08 |
| ministral-3:14b | 8.5 | 76% | 4020ms | 6789ms | $0.02 | $0.08 |

### Stage: rag_judge
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| ministral-3:8b | 6.0 | 40% | 3033ms | 4487ms | $0.01 | $0.05 |
| ministral-3:14b | 5.3 | 30% | 4092ms | 6944ms | $0.01 | $0.04 |
| qwen3.5:cloud | 5.1 | 30% | 20862ms | 22192ms | $0.09 | $0.04 |
| kimi-k2.5:cloud | 4.6 | 20% | 7098ms | 7969ms | $0.25 | $0.04 |
| kimi-k2.6:cloud | 4.6 | 20% | 7714ms | 8503ms | $0.24 | $0.04 |

### Stage: text_to_sql
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| qwen3.5:cloud | 9.2 | 80% | 54365ms | 56742ms | $0.14 | $0.05 |
| kimi-k2.5:cloud | 8.8 | 60% | 18930ms | 20058ms | $0.32 | $0.05 |
| kimi-k2.6:cloud | 8.3 | 45% | 24525ms | 25548ms | $0.32 | $0.05 |
| ministral-3:14b | 8.1 | 35% | 5268ms | 12383ms | $0.02 | $0.07 |
| ministral-3:8b | 7.5 | 25% | 7222ms | 10804ms | $0.02 | $0.08 |

### Stage: fast_classification
| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |
|---|---|---|---|---|---|---|
| ministral-3:8b | 9.8 | 95% | 1338ms | 1748ms | $0.01 | $0.02 |
| kimi-k2.5:cloud | 9.5 | 90% | 4778ms | 5102ms | $0.11 | $0.02 |
| kimi-k2.6:cloud | 9.5 | 90% | 4404ms | 4742ms | $0.11 | $0.02 |
| ministral-3:14b | 9.0 | 80% | 2080ms | 2848ms | $0.01 | $0.02 |
| qwen3.5:cloud | 8.8 | 75% | 17171ms | 17628ms | $0.06 | $0.02 |

### Recommendation
Paste this section manually after reviewing results:
- Heavy stages (emotion_shift, process_adherence, nli_policy): use ___________
- Fast stages (fast_classification): use ___________
- RAG judge: use ___________
- Embeddings: use ___________

Total benchmark rows: 675