# Process Adherence Validation Diagnosis (n=20, kimi-k2.6:cloud)

Compares new prompt (`_validate_process_adherence.json`) vs v5.1 full run (`process_adherence_groundtruth.json`).

## Summary

| CLOSER | SAME | WORSE |
|---:|---:|---:|
| 11 | 2 | 7 |

**Dominant category:** CLOSER

**Root cause:** Parser/scorer needs fuzzy step_key matching against STEP_KEY_TO_LABEL — models use near-correct keys but exact key match fails.

**Recommended next fix:** Add Levenshtein/substring matching in `ground_truth_scorer.py` `_resolve_step_token` / `_canonicalize_steps` (not another prompt change).

## Examples

### pa_001 (CLOSER)
- Reference missing: `['Verify refund eligibility window, Confirm refund method and timeline, Close with summary and next steps']`
- Old keys: `[]` → F1=0.0
- New keys: `['verify_refund_eligibility_window', 'close_with_summary_and_next_steps']` → F1=0.0
- New response preview: `{"missing_sop_steps":["verify_refund_eligibility_window","close_with_summary_and_next_steps"],"detected_topic":"refund_request","is_resolved":false,"efficiency_score":4,"justification":"The agent acknowledged the refund request and collected the account number, but failed to verify whether the refun...`

### pa_002 (CLOSER)
- Reference missing: `['Confirm customer understanding, Close with follow-up path']`
- Old keys: `[]` → F1=0.286
- New keys: `['acknowledge_billing_concern', 'confirm_customer_understanding', 'close_with_follow_up_path']` → F1=0.4
- New response preview: ````json
{
  "missing_sop_steps": [
    "acknowledge_billing_concern",
    "confirm_customer_understanding",
    "close_with_follow_up_path"
  ],
  "detected_topic": "billing_issue",
  "is_resolved": false,
  "efficiency_score": 4,
  "justification": "The agent identified the charge source (equipment...`

### pa_003 (CLOSER)
- Reference missing: `['Collect device or account context, Validate issue resolution, Document next escalation path']`
- Old keys: `[]` → F1=0.0
- New keys: `['acknowledge_the_technical_issue', 'collect_device_or_account_context', 'run_step_by_step_troubleshooting', 'validate_issue_resolution', 'document_next_escalation_path']` → F1=0.0
- New response preview: `{"missing_sop_steps":["acknowledge_the_technical_issue","collect_device_or_account_context","run_step_by_step_troubleshooting","validate_issue_resolution","document_next_escalation_path"],"detected_topic":"technical_support","is_resolved":false,"efficiency_score":2,"justification":"The agent never a...`
