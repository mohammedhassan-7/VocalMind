# PA Fuzzy Scorer Validation

## Part 2 — 20-sample re-score (kimi-k2.6 validation set)

- Fuzzy threshold: **0.85**
- Mean F1: **0.450 → 0.568**
- Fuzzy matches logged: **16**

## Part 3 — CLOSER samples (11)

| sample | model_key(s) | fuzzy match | sim | old F1 | new F1 | Δ |
|---|---|---|---:|---:|---:|---:|
| pa_001 | `verify_refund_eligibility_window`, `close_with_summary_and_next_steps` | (exact or ref-parse fix) | — | 0.86 | 0.80 | -0.06 |
| pa_002 | `acknowledge_billing_concern`, `confirm_customer_understanding`, `close_with_follow_up_path` | (exact or ref-parse fix) | — | 0.50 | 0.67 | +0.17 |
| pa_003 | `acknowledge_the_technical_issue`, `collect_device_or_account_context`, `run_step_by_step_troubleshooting`, `validate_issue_resolution` | (exact or ref-parse fix) | — | 0.57 | 0.75 | +0.18 |
| pa_004 | `acknowledge_access_issue`, `verify_user_identity`, `close_with_prevention_advice` | (exact or ref-parse fix) | — | 0.50 | 0.67 | +0.17 |
| pa_010 | `acknowledge_billing_concern`, `confirm_customer_understanding`, `close_with_follow_up_path` | (exact or ref-parse fix) | — | 0.57 | 0.67 | +0.10 |
| pa_011 | `collect_device_or_account_context`, `run_step_by_step_troubleshooting` | (exact or ref-parse fix) | — | 0.80 | 0.67 | -0.13 |
| pa_013 | `greet_and_confirm_intent_to_open_account` | (exact or ref-parse fix) | — | 1.00 | 1.00 | +0.00 |
| pa_014 | `acknowledge_and_reassure_the_customer`, `confirm_card_status_and_freeze_if_needed` | (exact or ref-parse fix) | — | 0.80 | 0.80 | +0.00 |
| pa_015 | `acknowledge_the_fee_concern`, `verify_the_fee_against_account_history_and_policy`, `check_waiver_authority_and_frequency_cap` | (exact or ref-parse fix) | — | 1.00 | 1.00 | +0.00 |
| pa_018 | `collect_order_identifier` | (exact or ref-parse fix) | — | 0.80 | 0.67 | -0.13 |
| pa_019 | `verify_account_and_charge_details`, `explain_charge_source_or_correction` | (exact or ref-parse fix) | — | 0.75 | 0.67 | -0.08 |
| pa_021 | `acknowledge_access_issue` | (exact or ref-parse fix) | — | 1.00 | 1.00 | +0.00 |

## Over-matching review (similarity 0.85–0.92)

**Borderline matches found — review for semantic correctness:**
- `Verify customer identity` → `verify_user_identity` (Verify user identity) sim=0.909
- `Acknowledge fee concern` → `acknowledge_the_fee_concern` (Acknowledge the fee concern) sim=0.92
- `Verify account and fee details` → `verify_account_and_charge_details` (Verify account and charge details) sim=0.889

**Over-matching found:** review required (see above)

**Recommend full re-score (765 obs):** yes


## Part 4 — Full PA re-score (765 obs)

| Model | v5.1 F1 | fuzzy F1 | v5.1 exact% | fuzzy exact% |
|---|---:|---:|---:|---:|
| kimi-k2.6:cloud | 0.508 | 0.539 | 35% | 37% |
| kimi-k2.5:cloud | 0.443 | 0.471 | 33% | 37% |
| qwen3.5:cloud | 0.421 | 0.453 | 31% | 34% |
| ministral-3:8b | 0.192 | 0.200 | 6% | 7% |
| ministral-3:14b | 0.138 | 0.149 | 3% | 3% |

**New PA winner:** `kimi-k2.6:cloud` — F1=0.539
