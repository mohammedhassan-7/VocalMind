# Model Selection Brief v10 (One Page)

Generated: 2026-06-16 15:38 UTC
Source: `D:\University\Grad\VocalMind\infra\benchmarks\reports\overnight_20260614\final_run_es_nli_8models_v10.json`

## Coverage
- emotion_shift rows: 1360/1360
- nli_policy rows: 1376/1376

## Recommended Routing (Current Best)
- OLLAMA_EMOTION_SHIFT_MODEL: `ministral-3:8b`
- OLLAMA_NLI_MODEL: `qwen3.5:cloud`

## Why These Models
- emotion_shift winner `ministral-3:8b`: exact=54.1%, parseable=90.6%, p50=74352ms, n=170.
- Rationale: best GT exact on friction-root-cause interpretation while keeping parseability strong.
- nli_policy winner `qwen3.5:cloud`: exact=60.5%, parseable=82.6%, p50=124371ms, n=172.
- Rationale: best policy classification exactness under parseability and latency tie-breakers.

## Top Contenders Snapshot
- emotion_shift top 3:
  - ministral-3:8b: exact=54.1%, parseable=90.6%, p50=74352ms, n=170
  - kimi-k2.5:cloud: exact=51.8%, parseable=86.5%, p50=93046ms, n=170
  - deepseek-v3.1:671b: exact=51.2%, parseable=85.9%, p50=96445ms, n=170
- nli_policy top 3:
  - qwen3.5:cloud: exact=60.5%, parseable=82.6%, p50=124371ms, n=172
  - ministral-3:14b: exact=58.1%, parseable=69.2%, p50=93896ms, n=172
  - ministral-3:8b: exact=51.2%, parseable=74.4%, p50=86521ms, n=172
