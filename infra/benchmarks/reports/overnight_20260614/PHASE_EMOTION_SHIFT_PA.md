# VocalMind — emotion_shift v2 Full Re-run + PA Diagnosis

**Generated:** 2026-06-15

---

## Part 1 — emotion_shift full re-run (n=170 × 3 models = 510)

**Prompt confirmed wired:** `benchmark_ollama_cloud.py` uses `EMOTION_SHIFT_SYSTEM` from `prompt_constants.py` (closed labels, few-shots, strict JSON) + `json_mode=True` for `emotion_shift`.

| | |
|---|---|
| **Time estimate** | ~2.0 h (510 calls @ 20 rpm + ~20s latency) |
| **Actual** | **2h 50m** (10,214s) |

### Results vs v5.1 baseline

| Model | v5.1 exact(all) | v2 exact(all) | v5.1 parseable% | v2 parseable% | v5.1 exact(parseable) | v2 exact(parseable) |
|---|---:|---:|---:|---:|---:|---:|
| **kimi-k2.5:cloud** | 37% | **53%** | 54% | **100%** | 68% | 53% |
| kimi-k2.6:cloud | 24% | 48% | 33% | **100%** | 71% | 48% |
| ministral-3:14b | 26% | 48% | 78% | **100%** | 34% | 48% |

### kimi-k2.5 accuracy-when-parseable check

At v5.1, kimi looked best *among parseable* (68%) but only 54% of outputs were scoreable — so headline exact(all) was 37%. After the prompt fix, **100% parseable** and **53% exact(all)** — the reliability gap is gone and kimi leads on the metric that matters for production (no silent `Unknown` fallback).

Exact(parseable) dropped 68%→53% because the old “among parseable” pool excluded the hardest 46% of samples; at 100% parseable, exact(all) = exact(parseable).

### New recommended winner

**`kimi-k2.5:cloud`** — only model with 100% parseable *and* highest exact(all) at 53%. ministral-3:14b tied at 48% exact but no longer wins on reliability; kimi is now both reliable and most accurate.

**Production config decision:** Switch heavy emotion_shift to kimi-k2.5:cloud (or keep kimi-k2.6 at 48% if latency/cost differs).

Artifacts: `emotion_shift_v2.json`, `emotion_shift_v2_groundtruth.json`, `EMOTION_SHIFT_V2_REPORT.md`

---

## Part 2 — PA failure diagnosis (n=20, no new API calls)

| CLOSER | SAME | WORSE |
|---:|---:|---:|
| **11** | 2 | 7 |

**Dominant category:** CLOSER

**Root cause:** Scorer/parser alignment — models now return correct *ideas* as `step_key` strings (`verify_refund_eligibility_window`, `confirm_customer_understanding`) but `ground_truth_scorer.py` fuzzy matching still misses partial key overlap vs reference human-readable labels. The catalog did not hurt most samples; F1=0 on many CLOSER cases is a **scoring** issue, not reasoning.

**Recommended next fix:** Add fuzzy step_key matching in `ground_truth_scorer.py` (`_resolve_step_token` / `_canonicalize_steps` — Levenshtein or prefix match against `STEP_KEY_TO_LABEL`), **not** another prompt iteration.

### Examples (CLOSER)

**pa_002** — new keys hit the right steps, F1 improved 0.29→0.40:
- Ref missing: `Confirm customer understanding`, `Close with follow-up path`
- New keys: `confirm_customer_understanding`, `close_with_follow_up_path` (+ extra `acknowledge_billing_concern`)

**pa_003** — model lists correct technical_support keys including all three ref steps, F1 still 0 (scorer mismatch):
- Ref: `Collect device or account context`, `Validate issue resolution`, `Document next escalation path`
- New keys: `collect_device_or_account_context`, `validate_issue_resolution`, `document_next_escalation_path` (+ over-flagged acknowledge/troubleshooting)

**pa_001** — new format works, keys partially right:
- New keys: `verify_refund_eligibility_window`, `close_with_summary_and_next_steps` (missing `confirm_refund_method_and_timeline`)

Full detail: `PA_DIAGNOSIS.md`

---

## Status

- **emotion_shift:** Confirmed at n=170 — prompt fix is real; kimi-k2.5 recommended for production.
- **process_adherence:** Diagnosis complete; next step is scorer fuzzy matching, no PA re-run yet.
