# FR-5 Friction Diagnosis + NLI v9 — Change Report

**Date:** 2026-06-15

## What changed

### FR-5: Emotion shift → **Friction root-cause diagnosis**

The reasoning engine no longer classifies sarcasm / passive_aggression / cross_modal (upstream emotion pipeline owns that).

**New closed labels:**
| Label | Meaning |
|---|---|
| `interruption` | Agent talked over / overlapping speech |
| `dismissive_tone` | Curt, blaming, impatient agent language |
| `missing_acknowledgment` | Jumped to script/verification without acknowledging concern |
| `none` | No agent behavioral friction |

**Input now includes:** `Detected emotion (pipeline): <anger|frustration|…>` + transcript context.

**Output JSON key:** `friction_root_cause` (mirrored in `shift_type` / `dissonance_type`).

**GT remapped:** `infra/scripts/remap_friction_diagnosis_gt.py` → `ollama_cloud_ground_truth_v2.json`

| Label | n (emotion_shift) |
|---|---:|
| interruption | 2 |
| dismissive_tone | 12 |
| missing_acknowledgment | 67 |
| none | 89 |

### NLI v9

- Stronger few-shots (Policy Hallucination vs Contradiction, at-threshold Benign Deviation)
- Scorer accepts defensible PH↔Contradiction and BD↔Contradiction ($50 threshold) matches when justification supports it

## Rescored overnight checkpoints (old model responses, new rubric)

| Stage | Model | v7 exact | v9 exact | Δ |
|---|---|---:|---:|---:|
| **nli_policy** | ministral-3:8b | 52% | **70%** | +18 pp |
| **nli_policy** | kimi-k2.5 | 49% | **60%** | +11 pp |
| emotion_shift (friction) | kimi-k2.5 | 53%* | **13%** | task changed |

\*Old v7 metric was sarcasm/PA/cross_modal — not comparable.

**NLI at 70%** on existing checkpoints without new API calls (scorer + rubric alignment).

**Friction scores are low on old checkpoints** because models still output `sarcasm` / `cross_modal` — **requires re-benchmark** with new prompts to measure real FR-5 performance.

## Files touched

- `backend/app/llm_trigger/prompt_constants.py` — friction + NLI prompts
- `backend/app/llm_trigger/prompts.py` — human task text
- `backend/app/llm_trigger/schemas.py` — label descriptions
- `backend/app/llm_trigger/service.py` — runs friction chain when negative acoustic; no Sarcasm fallback
- `infra/scripts/ground_truth_scorer.py` — friction + NLI scoring
- `infra/scripts/remap_friction_diagnosis_gt.py` — GT migration

## Next step

Re-benchmark with production prompts (~2.5h):

```bash
python infra/scripts/benchmark_ollama_cloud.py \
  --ground-truth infra/benchmarks/ollama_cloud_ground_truth_v2.json \
  --stages emotion_shift,nli_policy \
  --models kimi-k2.5:cloud,ministral-3:8b \
  --skip-judge
```
