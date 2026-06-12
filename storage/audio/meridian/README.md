# Meridian Trust Bank Scripted Call Audio Fixtures

Generated from the annotated 2-agent scripts in `scripts/` using the
Gemini TTS pipeline (`Data/tts-audio-generator/generate_audio.py`).

Ground truth in `evaluation/` (one JSON per call + `manifest.json`) is the
source for end-to-end checks: STT transcript accuracy, speaker role accuracy,
emotion label accuracy, RAG trigger recall, and agent assignment.

## Filename Convention

`CALL_<NN>_<agent_lowercase>_<scenario>.wav`

The agent token embedded in the filename is the **primary agent** for the
call. The auto-ingest watcher
(`backend/app/core/audio_folder_watcher.py`) uses this token to assign the
interaction to the correct seeded agent on first detection.

## Agents (Seeded)

Five primary agents are seeded into the Meridian Trust Bank organization
with the same performance gradient design as NexaLink:

| Agent | Gender | Performance Tier | Notes |
|---|---|---|---|
| **Sarah**   | F | **HIGH**   | Senior personal banker; precise on regulatory disclosures |
| **Tyler**   | M | **LOW**    | Three distinct failure modes: forbidden phrase, wrong information (rate quoted from memory), dismissive tone |
| **Andre**   | M | MEDIUM | Business-banking specialist; methodical cadence |
| **Jasmine** | F | MEDIUM | Fraud-prevention specialist; calm warm low-mid register |
| **Karen**   | F | MEDIUM | Complaints / retention banker; holds steady under pressure |

All calls have exactly two speakers — `AGENT` and `CUSTOMER`. Off-line
actions are handled via back-office tickets (Manager Approval, Reg E
Adjudication, Fraud Operations, Data Compliance, BSA Officer) with the SLA
disclosed on-call.

## Audio File Index

| File | Scenario | Primary Agent | Ground Truth |
|---|---|---|---|
| `CALL_21_sarah_kyc_account_opening.wav` | New account opening; full CIP + OFAC + Reg DD disclosure | Sarah | evaluation/CALL_21_kyc_account_opening.json |
| `CALL_22_sarah_wire_transfer_verification.wav` | Outbound $5K wire; Enhanced Verification + OFAC beneficiary screen | Sarah | evaluation/CALL_22_wire_transfer_verification.json |
| `CALL_23_sarah_mortgage_inquiry_no_rate_quote.wav` | Mortgage rate inquiry; TILA-compliant refusal to quote from memory | Sarah | evaluation/CALL_23_mortgage_inquiry_no_rate_quote.json |
| `CALL_24_tyler_overdraft_dispute_over_cap.wav` | Overdraft fee dispute over $250 cap; forbidden phrase used | Tyler | evaluation/CALL_24_overdraft_dispute_over_cap.json |
| `CALL_25_tyler_loan_rate_misquote.wav` | Auto loan inquiry; rate quoted from memory (BNK-REG-RULE-003 FAIL) | Tyler | evaluation/CALL_25_loan_rate_misquote.json |
| `CALL_26_tyler_atm_dispute_rude_tone.wav` | Reg E ATM dispute; rude / dismissive tone | Tyler | evaluation/CALL_26_atm_dispute_rude_tone.json |
| `CALL_27_andre_business_loan_inquiry.wav` | Small-business equipment loan inquiry; Reg Z disclosure path | Andre | evaluation/CALL_27_business_loan_inquiry.json |
| `CALL_28_andre_business_account_signers.wav` | Add authorized signer to business account; CIP for new signer at branch | Andre | evaluation/CALL_28_business_account_signers.json |
| `CALL_29_andre_check_fraud_business.wav` | Three forged checks on business account; full SOP-03 procedure | Andre | evaluation/CALL_29_check_fraud_business.json |
| `CALL_30_jasmine_card_fraud_unauthorized_charges.wav` | Card-present-elsewhere fraud; Reg E provisional credit + Manager Approval ticket | Jasmine | evaluation/CALL_30_card_fraud_unauthorized_charges.json |
| `CALL_31_jasmine_elder_financial_exploitation.wav` | Suspected IRS-impersonation scam; BNK-FRAUD-RULE-007 pause + decline | Jasmine | evaluation/CALL_31_elder_financial_exploitation.json |
| `CALL_32_jasmine_suspected_aml_pattern.wav` | Structuring pattern; BNK-REG-RULE-010 no-tip-off rule executed silently | Jasmine | evaluation/CALL_32_suspected_aml_pattern.json |
| `CALL_33_karen_account_closure_complaint.wav` | Long-tenure customer closure complaint; partial retention save | Karen | evaluation/CALL_33_account_closure_complaint.json |
| `CALL_34_karen_overdraft_fee_waiver.wav` | Vacation-week overdraft waiver within authority; transfer protection enabled | Karen | evaluation/CALL_34_overdraft_fee_waiver.json |
| `CALL_35_karen_abuse_3_strike_termination.wav` | Abusive customer; BNK-CC-RULE-016 3-strike termination | Karen | evaluation/CALL_35_abuse_3_strike_termination.json |

## Evaluation Targets

| Capability | Target | Ground Truth Field |
|---|---:|---|
| STT word error rate | <= 0.15 | `turns[].text` |
| Speaker role accuracy | >= 0.90 | `turns[].speaker` |
| Emotion accuracy (7-label canonical) | >= 0.70 | `turns[].emotion_gt` |
| RAG trigger recall | >= 0.80 | `coverage` |
| Agent assignment | 1.00 | `primary_agent` |

The 7 canonical emotion labels are
`happy | angry | sad | frustrated | surprised | neutral | unknown`
(per `backend/app/core/inference_contracts.py::normalize_emotion_label`).
Rich TTS emotion tags in the scripts are projected onto this label space by
`Data/tts-audio-generator/emotion_map.py`.

## Notes

- `.wav` files in this folder are not committed to git; they are processed
  locally by the auto-ingest watcher and their filename encodes the agent.
- Drop a new audio file matching the naming convention into this folder while
  the backend is running and it will be auto-queued for the full processing
  pipeline (transcribe -> diarize -> emotion -> trigger evaluation).
- All calls are exactly two speakers (`AGENT` + `CUSTOMER`). Meridian
  policies (BNK-CC-RULE-*, BNK-SEC-RULE-*, BNK-FIN-RULE-*, BNK-REG-RULE-*,
  BNK-FRAUD-RULE-*) are ingested separately via
  `storage/docs/meridian/` and indexed in Qdrant for RAG retrieval.
