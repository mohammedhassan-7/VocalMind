# NexaLink Scripted Call Audio Fixtures

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

Five primary agents are seeded into the NexaLink organization with a
deliberate performance gradient so QA dashboards have signal:

| Agent | Gender | Performance Tier | Notes |
|---|---|---|---|
| **Priya**  | F | **HIGH**   | Clean SOP, full A.C.E.S., compliant closings |
| **Daniel** | M | **LOW**    | Three distinct failure modes: forbidden phrase, wrong information, dismissive tone |
| **Marcus** | M | MEDIUM | Methodical tech-support cadence; mostly compliant |
| **Aisha**  | F | MEDIUM | Warm reassuring register; security / privacy specialist |
| **Hannah** | F | MEDIUM | Composed under pressure; retention + 3-strike termination |

All calls have exactly two speakers — `AGENT` and `CUSTOMER`. No escalation
to Tier 2 / Tier 3. When a call requires off-line action, the agent opens a
back-office ticket (Manager Approval, Data Compliance, Network Operations,
Revenue Assurance, Field Service) and tells the customer the SLA.

## Audio File Index

| File | Scenario | Primary Agent | Ground Truth |
|---|---|---|---|
| `CALL_01_priya_refund_outage.wav` | Refund credit for 48-hour internet outage | Priya | evaluation/CALL_01_refund_outage.json |
| `CALL_02_daniel_billing_dispute.wav` | Disputed charges over agent cap; forbidden phrase used | Daniel | evaluation/CALL_02_billing_dispute.json |
| `CALL_03_marcus_tech_support_slow_internet.wav` | ESL customer slow-internet walkthrough | Marcus | evaluation/CALL_03_tech_support_slow_internet.json |
| `CALL_04_aisha_access_recovery_fraud.wav` | Elderly customer suspected fraud; full SEC-RULE-008 procedure | Aisha | evaluation/CALL_04_access_recovery_fraud.json |
| `CALL_05_hannah_retention_abuse.wav` | Retention call turns abusive; 3-strike termination | Hannah | evaluation/CALL_05_retention_abuse.json |
| `CALL_06_priya_pin_reset.wav` | Security PIN reset, 3-of-5 verification | Priya | evaluation/CALL_06_pin_reset.json |
| `CALL_07_priya_plan_upgrade.wav` | Home internet upgrade 100 to 500 Mbps | Priya | evaluation/CALL_07_plan_upgrade.json |
| `CALL_08_priya_cooling_off.wav` | Cooling-off cancellation within 14 days | Priya | evaluation/CALL_08_cooling_off.json |
| `CALL_09_daniel_billing_dispute_over_cap.wav` | $340 erroneous charge over $200 cap; forbidden phrase + weak A.C.E.S. | Daniel | evaluation/CALL_09_billing_dispute_over_cap.json |
| `CALL_10_daniel_refund_wrong_info.wav` | Sub-threshold outage credit denied with wrong numbers (FIN-RULE-010 violated) | Daniel | evaluation/CALL_10_refund_wrong_info.json |
| `CALL_11_daniel_fraud_dismissive_tone.wav` | Suspected fraudulent charge; rude dismissive tone | Daniel | evaluation/CALL_11_fraud_dismissive_tone.json |
| `CALL_12_marcus_router_setup.wav` | New router setup walkthrough; CS-RULE-009 re-engagement | Marcus | evaluation/CALL_12_router_setup.json |
| `CALL_13_marcus_wifi_speed_denied.wav` | Speed complaint with WiFi-only test; FIN-RULE-003 correctly invoked | Marcus | evaluation/CALL_13_wifi_speed_denied.json |
| `CALL_14_marcus_missed_appointment.wav` | Missed tech appointment, 1st occurrence; $25 ADJ-COURTESY | Marcus | evaluation/CALL_14_missed_appointment.json |
| `CALL_15_aisha_2fa_recovery.wav` | Two-factor authenticator recovery after lost phone | Aisha | evaluation/CALL_15_2fa_recovery.json |
| `CALL_16_aisha_unauthorized_access.wav` | Suspected unauthorized access; full SEC-RULE-008 freeze procedure | Aisha | evaluation/CALL_16_unauthorized_access.json |
| `CALL_17_aisha_data_deletion_gdpr.wav` | GDPR / CCPA data deletion request | Aisha | evaluation/CALL_17_data_deletion_gdpr.json |
| `CALL_18_hannah_cancellation_retention.wav` | Cancellation intent; successful retention save | Hannah | evaluation/CALL_18_cancellation_retention.json |
| `CALL_19_hannah_speed_downgrade_etf_waiver.wav` | Verified slow speed; ETF waiver via Manager Approval ticket | Hannah | evaluation/CALL_19_speed_downgrade_etf_waiver.json |
| `CALL_20_hannah_abuse_3_strike.wav` | Abusive customer; CS-RULE-016 3-strike termination | Hannah | evaluation/CALL_20_abuse_3_strike.json |

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
- All calls are exactly two speakers (`AGENT` + `CUSTOMER`). Legacy
  Tier 2 / Tier 3 escalation scripts have been retired; the corresponding
  call IDs (CALL_02, CALL_04, CALL_05) were re-authored as 2-agent versions
  with the same customer personas.
