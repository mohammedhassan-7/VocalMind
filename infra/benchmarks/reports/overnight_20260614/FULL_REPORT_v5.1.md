# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v5.1

**Generated:** 2026-06-15 15:30 UTC
**Primary metric:** ground-truth exact match (objective comparison, no LLM judge)
**Source:** Re-scored from saved raw responses in `overnight_20260614/` (zero new API calls)

## Metric definitions (read together)

**Exact (all)** — fraction of all samples with an exact ground-truth match. This is the headline comparability number from v5 (includes unparseable as non-exact).

**Exact (parseable)** — among samples where output was scoreable, what fraction matched exactly. This isolates reasoning quality from formatting/schema failures.

**Parseable %** — fraction of samples where the scorer could extract a verdict at all (1 − unparseable rate). Low parseable % means the model ignored output schema, not necessarily that it reasoned incorrectly.

These three numbers must be read together: a model can score high on accuracy-when-parseable but low on exact-all if it frequently returns unparseable output.

## Run status (unchanged from v3)

| Stage | Observations | Errors |
|---|---:|---:|
| emotion_shift | 510 | 0 |
| process_adherence | 765 | 0 |
| nli_policy | 1032 | 0 |
| rag_judge | 300 | 0 |
| text_to_sql | 150 | 0 |
| fast_classification | 462 | 0 |

## Part 1 — Split metrics (all stages)

### emotion_shift
> Exact/partial match against reference label or structured answer.

| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:14b | 15% | 20% | 74% | 1.47 | 11377 | 170 |
| kimi-k2.5:cloud | 13% | 27% | 48% | 1.29 | 20844 | 170 |
| kimi-k2.6:cloud | 7% | 40% | 18% | 0.71 | 24826 | 170 |

### process_adherence
> F1-based set match on missing SOP steps.

| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| kimi-k2.6:cloud | 43% | 45% | 95% | 5.46 | 40420 | 153 |
| qwen3.5:cloud | 35% | 51% | 69% | 4.30 | 56450 | 153 |
| kimi-k2.5:cloud | 30% | 37% | 82% | 4.04 | 48748 | 153 |
| ministral-3:14b | 12% | 28% | 42% | 1.22 | 21147 | 153 |
| ministral-3:8b | 12% | 28% | 42% | 1.23 | 18950 | 153 |

- **kimi-k2.6:cloud** mean F1: 0.546
- **qwen3.5:cloud** mean F1: 0.430
- **kimi-k2.5:cloud** mean F1: 0.404
- **ministral-3:8b** mean F1: 0.123
- **ministral-3:14b** mean F1: 0.122

### nli_policy
> Exact/partial match against reference label or structured answer.

| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:8b | 70% | 70% | 100% | 6.98 | 2765 | 172 |
| kimi-k2.5:cloud | 60% | 60% | 100% | 6.05 | 13506 | 172 |
| kimi-k2.6:cloud | 59% | 59% | 100% | 5.93 | 11894 | 172 |

### rag_judge
> Exact/partial match against reference label or structured answer.

| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:8b | 95% | 96% | 99% | 9.73 | 2603 | 150 |
| kimi-k2.6:cloud | 81% | 82% | 99% | 9.03 | 13139 | 150 |

### text_to_sql
> Execution-based scoring (unchanged from v3). Parseable ≈ 100%.

| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.5:cloud | 54% | 54% | 100% | 6.48 | 55920 | 50 |
| kimi-k2.6:cloud | 38% | 38% | 100% | 5.60 | 14604 | 50 |
| ministral-3:8b | 20% | 20% | 100% | 2.96 | 3821 | 50 |

### fast_classification
> Exact/partial match against reference label or structured answer.

| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |
|---|---:|---:|---:|---:|---:|---:|
| ministral-3:14b | 69% | 69% | 100% | 8.25 | 1370 | 154 |
| kimi-k2.6:cloud | 68% | 68% | 100% | 8.12 | 3568 | 154 |
| ministral-3:8b | 68% | 68% | 100% | 8.05 | 1309 | 154 |

## Part 2 — emotion_shift label canonicalization

Benchmark models use inconsistent shift-type vocabulary. The v5 scorer used alias/fuzzy matching; v5.1 adds an explicit conservative synonym map (not partial credit for wrong answers).

### Rubric reference

- Task (prompts.py): "Detect cross-modal contradictions between text and acoustic emotion."
- Classification (prompts.py): "classify type (e.g., Sarcasm, Passive-Aggression)." 
- Ground-truth categories: `sarcasm`, `passive_aggression`, `cross_modal`, `none`.

### Mappings applied

**cross_modal** — Rubric (prompts.py): "Detect cross-modal contradictions between text and acoustic emotion." Variants naming text/acoustic or semantic/acoustic mismatch are the same category.
- `acoustic textual` → `cross_modal`
- `acoustic-textual` → `cross_modal`
- `cross modal contradiction` → `cross_modal`
- `cross_modal_contradiction` → `cross_modal`
- `emotion text discrepancy` → `cross_modal`
- `emotion_text_discrepancy` → `cross_modal`
- `emotional disconnect` → `cross_modal`
- `emotional discrepancy` → `cross_modal`
- `emotional incongruence` → `cross_modal`
- `emotional misalignment` → `cross_modal`
- `emotional_disconnect` → `cross_modal`
- `emotional_discrepancy` → `cross_modal`
- `emotional_incongruence` → `cross_modal`
- `emotional_misalignment` → `cross_modal`
- `neutral text vs negative acoustic` → `cross_modal`
- `neutral_text_vs_negative_acoustic` → `cross_modal`
- `positive text vs negative acoustic` → `cross_modal`
- `positive_service_text_vs_negative_acoustic_delivery` → `cross_modal`
- `positive_text_vs_negative_acoustic` → `cross_modal`
- `potential acoustic text mismatch` → `cross_modal`
- … and 18 more variants

**sarcasm** — Rubric (prompts.py): "classify type (e.g., Sarcasm, Passive-Aggression)." Direct sarcasm labels.
- `sarcasm frustration` → `sarcasm`
- `sarcasm/frustration` → `sarcasm`
- `sarcastic` → `sarcasm`
- `sarcastic inversion` → `sarcasm`

**passive_aggression** — Rubric few-shot (prompts.py): dissonance_type "Passive-Aggression" for polite text vs negative acoustic.
- `passive aggressive` → `passive_aggression`
- `passive-aggressive` → `passive_aggression`

**none** — True-negative samples: no dissonance / aligned text and acoustic emotion.
- `aligned` → `none`
- `n/a (no contradiction)` → `none`
- `neutral (no contradiction detected)` → `none`
- `neutral (no contradiction)` → `none`
- `no contradiction` → `none`
- `no cross modal` → `none`
- `no cross-modal` → `none`
- `no_contradiction` → `none`
- `not specified (no contradiction)` → `none`
- `true negative` → `none`

### Ambiguous / not mapped

- **Ambiguous terms (explicit blocklist):** 48 sample-label occurrences across all models
- **Unknown unmapped terms:** 69 occurrences

Top ambiguous labels seen in parseable JSON:
- `procedural_issue`: 18
- `SOP`: 6
- `procedural_violation`: 5
- `insufficient evidence`: 4
- `textual`: 4
- `masking`: 2
- `procedural_delay`: 2
- `procedural_friction`: 2
- `Policy`: 2
- `potential`: 1
- `procedural`: 1
- `training`: 1

Top unmapped labels (left as no_match):
- `customer_statement`: 3
- `textual_contradiction`: 2
- `policy_compliance`: 2
- `positive_service_text_vs_negative_acoustic_delivery`: 1
- `Procedural compliance vs. emotional resistance`: 1
- `procedural_context`: 1
- `agent_policy_stance_reversal`: 1
- `mixed-emotion`: 1
- `procedural_insensitivity`: 1
- `positive_semantic_content_negative_acoustic_delivery`: 1
- `minimization_vs_physiological_stress`: 1
- `lexical_positive_vs_inferred_acoustic_negative`: 1

### emotion_shift before / after canonicalization

| Model | Exact (all) | Exact (all) canon | Exact (parseable) | Exact (parseable) canon | Parseable % |
|---|---:|---:|---:|---:|---:|
| ministral-3:14b | 15% | 15% | 20% | 20% | 74% |
| kimi-k2.5:cloud | 13% | 13% | 27% | 27% | 48% |
| kimi-k2.6:cloud | 7% | 7% | 40% | 40% | 18% |

## Part 3 — Recommendations (split-metric framing)

### Production pipeline: parse failure behavior

`chains.py` `_invoke_chain_with_retry` retries only **transient API errors** (429, timeout, connection) up to 3× — **not** JSON/Pydantic parse failures. `analyze_emotion_shift` catches any chain failure (including parse errors) and returns degraded `EmotionShiftAnalysis` with `dissonance_type="Unknown"` and `insufficient_evidence=True`. **No re-prompt on parse failure.**

**Framing for emotion_shift:** reliability-first — parse failures degrade to `dissonance_type=Unknown` with no re-prompt; parseable % matters as much as accuracy-among-parseable.

**Updated emotion_shift winner: `ministral-3:14b`** (reliability-first).

- `kimi-k2.5:cloud`: 13% exact (all) / 27% among parseable / 48% parseable — highest accuracy when scoreable, but 52% unparseable.
- `ministral-3:14b`: 15% exact (all) / 20% among parseable / 74% parseable — more reliable JSON, lower reasoning accuracy.
- Production (`service.py`) does **not** retry on JSON parse failure; failures fall back to `dissonance_type=Unknown`. Recommend `ministral-3:14b` unless prompt/schema is tightened to raise kimi-k2.5 parseable % (stricter JSON-only instruction).

### Recommendation table

| Stage | Model | Exact (all) | Exact (parseable) | Parseable % | Verdict |
|---|---|---:|---:|---:|---|
| emotion_shift | `ministral-3:14b` | 15% | 20% | 74% | GT winner (reliability-first) |
| process_adherence | `kimi-k2.6:cloud` | 43% | 45% | 95% | GT winner (F1=0.55) |
| nli_policy | `ministral-3:8b` | 70% | 70% | 100% | GT winner |
| rag_judge | `ministral-3:8b` | 95% | 96% | 99% | GT winner |
| text_to_sql | `qwen3.5:cloud` | 54% | 54% | 100% | GT winner |
| fast_classification | `ministral-3:14b` | 69% | 69% | 100% | GT winner |

## What changed vs v3 (judge-driven)

| Stage | v3 judge winner | v5.1 GT winner | Changed? |
|---|---|---|---|
| emotion_shift | ministral-3:14b | ministral-3:14b | No |
| process_adherence | qwen3.5:cloud | kimi-k2.6:cloud | Yes |
| nli_policy | kimi-k2.5:cloud | ministral-3:8b | Yes |
| rag_judge | ministral-3:8b | ministral-3:8b | No |
| text_to_sql | qwen3.5:cloud | qwen3.5:cloud | No |
| fast_classification | ministral-3:14b | ministral-3:14b | No |

## process_adherence finding

F1-based GT scoring **confirms models genuinely struggle** on process_adherence (mean F1=0.32, exact-match=26%, judge avg=5.20). Low scores are not primarily a judge artifact.

## Unparseable responses (>10%)

- emotion_shift/ministral-3:14b: 26% unparseable
- emotion_shift/kimi-k2.5:cloud: 52% unparseable
- emotion_shift/kimi-k2.6:cloud: 82% unparseable
- process_adherence/ministral-3:14b: 58% unparseable
- process_adherence/ministral-3:8b: 58% unparseable
- process_adherence/kimi-k2.5:cloud: 18% unparseable
- process_adherence/qwen3.5:cloud: 31% unparseable

## Largest judge vs ground-truth divergences

### process_adherence / ministral-3:14b / pa_060
- Old judge: **20.0** | GT score: **0.0** (unparseable)
- Reference: No missing SOP steps. Complete adherence.
- GT details: extraction_error: unparseable JSON

### process_adherence / ministral-3:14b / pa_055
- Old judge: **15.0** | GT score: **0.0** (unparseable)
- Reference: Missing SOP steps: [Acknowledge billing concern, Verify account and charge details, Explain charge source or correction].
- GT details: extraction_error: unparseable JSON

### emotion_shift / ministral-3:14b / es_001
- Old judge: **10.0** | GT score: **0.0** (no_match)
- Reference: No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.
- GT details: false positive shift

### emotion_shift / kimi-k2.5:cloud / es_001
- Old judge: **10.0** | GT score: **0.0** (no_match)
- Reference: No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.
- GT details: legacy emotion label Sarcasm; use friction_root_cause

### emotion_shift / kimi-k2.6:cloud / es_001
- Old judge: **10.0** | GT score: **0.0** (no_match)
- Reference: No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.
- GT details: legacy emotion label Sarcasm; use friction_root_cause

## Appendix: Judge scores (secondary)

| Stage | Model | Old judge avg | Exact (all) | Exact (parseable) | Parseable % |
|---|---|---:|---:|---:|---:|
| emotion_shift | kimi-k2.5:cloud | 6.56 | 13% | 27% | 48% |
| emotion_shift | kimi-k2.6:cloud | 5.75 | 7% | 40% | 18% |
| emotion_shift | ministral-3:14b | 7.31 | 15% | 20% | 74% |
| process_adherence | kimi-k2.5:cloud | 5.34 | 30% | 37% | 82% |
| process_adherence | kimi-k2.6:cloud | 5.51 | 43% | 45% | 95% |
| process_adherence | ministral-3:14b | 4.15 | 12% | 28% | 42% |
| process_adherence | ministral-3:8b | 4.36 | 12% | 28% | 42% |
| process_adherence | qwen3.5:cloud | 6.65 | 35% | 51% | 69% |
| nli_policy | kimi-k2.5:cloud | 8.73 | 60% | 60% | 100% |
| nli_policy | kimi-k2.6:cloud | 8.70 | 59% | 59% | 100% |
| nli_policy | ministral-3:8b | 8.70 | 70% | 70% | 100% |
| rag_judge | kimi-k2.6:cloud | 8.18 | 81% | 82% | 99% |
| rag_judge | ministral-3:8b | 9.36 | 95% | 96% | 99% |
| text_to_sql | kimi-k2.6:cloud | 5.60 | 38% | 38% | 100% |
| text_to_sql | ministral-3:8b | 2.96 | 20% | 20% | 100% |
| text_to_sql | qwen3.5:cloud | 6.48 | 54% | 54% | 100% |
| fast_classification | kimi-k2.6:cloud | 8.18 | 68% | 68% | 100% |
| fast_classification | ministral-3:14b | 8.44 | 69% | 69% | 100% |
| fast_classification | ministral-3:8b | 8.28 | 68% | 68% | 100% |