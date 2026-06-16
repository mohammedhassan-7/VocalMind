# emotion_shift v2 Full Re-run Report

**Generated:** 2026-06-15 11:02 UTC
**Source:** `emotion_shift_v2.json` (2026-06-15T11:02:19.171068+00:00)
**Prompt:** closed label set + JSON mode (prompt_constants.py)

## Comparison vs v5.1

| Model | v5.1 exact(all) | v2 exact(all) | v5.1 parseable% | v2 parseable% | v5.1 exact(parseable) | v2 exact(parseable) | GT avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| kimi-k2.5:cloud | 37% | 53% | 54% | 100% | 68% | 53% | 5.29 |
| kimi-k2.6:cloud | 24% | 48% | 33% | 100% | 71% | 48% | 4.76 |
| ministral-3:14b | 26% | 48% | 78% | 100% | 34% | 48% | 4.76 |

**New recommended winner:** `kimi-k2.5:cloud` — parseable=100%, exact(parseable)=53%, exact(all)=53%
