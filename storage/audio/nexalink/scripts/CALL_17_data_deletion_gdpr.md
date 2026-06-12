# CALL_17 — GDPR/CCPA Data Deletion Request

```yaml
call_id: CALL_17_data_deletion_gdpr
duration_estimate: 6m 30s
turns: 46
sop_primary: SOP-04 (Account Access / Privacy Operations)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-007, CS-RULE-011, CS-RULE-014, CS-RULE-015, SEC-RULE-001, SEC-RULE-002, SEC-RULE-009, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 4.9 - Data Deletion Requests, Section 5.2 - Account Closure Pre-conditions]
customer_profile:
  name: "Henrik Lindqvist"
  account_number: "6230-1175-82"
  voice_hint: "male, mid-30s, light Swedish accent, calm and informed about data rights"
agent_profile:
  name: "Aisha"
  voice_hint: "female, late 30s, warm low-mid register, deliberate and reassuring"
emotional_arc: "neutral -> informed -> cooperative -> satisfied"
expected_outcome: "Customer has cancelled service and now requests deletion of all retained personal data under GDPR/CCPA. Aisha confirms account is closed, explains the 30-day deletion timeline and the retention exceptions (regulatory billing records held for the legally required period). Opens a Data Deletion ticket routed to the Data Compliance Officer per SEC-RULE-009. ONE minor CS-RULE-007 slip — Aisha takes a longer silent moment while pulling records. PASS overall with minor coachable moment."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002, SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Privacy data-use statement | T15 | SEC-RULE-002 — PASS |
| MINOR slip: extended silence without re-engagement | T19–T20 | CS-RULE-007 — MINOR FAIL |
| Explains 30-day deletion + retention exceptions | T23–T29 | SEC-RULE-009 — PASS |
| Data Deletion ticket routed to Data Compliance Officer | T33 | SEC-RULE-009 — PASS |
| Ticket workflow + SLA disclosed | T33–T35 | CS-RULE-014, CS-RULE-015 — PASS |
| A.C.E.S. light — Acknowledge + Clarify | T17, T21 | CS-RULE-011 — PASS |
| Root cause / context | T39 | CS-RULE-018 — PASS |
| Resolution summary | T41 | CS-RULE-019 — PASS |
| Anything else + case ref + survey | T44, T46 | CS-RULE-020, CS-RULE-021 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Aisha. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"And this call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | neutral:3 | normal | mid | normal
"Hello, this is Henrik Lindqvist. I cancelled my service with NexaLink about three weeks ago, and I'm calling to make a formal request that you delete all my personal data from your systems."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Hello Mr. Lindqvist. Thank you for being clear about that — data deletion requests are a specific procedure, and I can absolutely take that for you on this call."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a personal data deletion request, and I can certainly help you with that. Before I look at anything on the account, I'll need to verify your identity. Could you start with the account number, even though the account itself is closed?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Six-two-three-zero, one-one-seven-five, eight-two."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And could you confirm the last four digits of the payment method that was on file?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Five-five-zero-one."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And the full name on the account, exactly as it appeared?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Henrik Erik Lindqvist."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That all matches. You're fully verified, Mr. Lindqvist — even on a closed account."
```

```
[T12] CUSTOMER | satisfied:2 | normal | mid | normal
"Good."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"And I can confirm I see the account status — it was closed twenty-three days ago, final bill paid in full, no outstanding balance. Equipment return marked received. That's all clean."
```

```
[T14] CUSTOMER | cooperative:2 | normal | mid | normal
"Yes, that matches what I have."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"Your data is used solely for service provisioning and support quality, in accordance with our Privacy Policy — and where you have a regulatory right to deletion, we honour that under our Data Compliance process."
```

```
[T16] CUSTOMER | curious:3 | normal | mid | normal
"That's exactly what I wanted to ask about. I'm exercising my right to erasure under GDPR. I'm a Swedish citizen — does that apply to my data with you?"
```

```
[T17] AGENT | thoughtful:3 | normal | mid | normal
"It does. NexaLink processes deletion requests under both GDPR for European subjects and CCPA for California residents, and we apply the broader of the two protections regardless of which framework you cite — so whichever applies to you, the outcome is the same."
```

```
[T18] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T19] AGENT | professional:3 | slow | mid | normal | (typing)
"One moment while I pull the data inventory associated with the account so I can walk you through exactly what's affected."
```

```
[T20] CUSTOMER | calm:2 | normal | mid | normal | (pause)
"Sure, take your time."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Alright. So there are three categories I want to walk through, because they have different rules — and I think you'll want to know the distinction."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Please."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Category one is non-essential personal data — your name, address, contact details, service preferences, support call history, marketing-consent records. All of that will be purged within thirty days of the confirmed deletion request. After that, it is permanently removed."
```

```
[T24] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"Category two is data we're legally required to retain for a fixed period — primarily billing records, tax records, and lawful intercept logs. By US tax law and telecom regulation, those need to be held for seven years from the date of the last transaction. We cannot delete those before then, even on request. That's not a NexaLink decision — it's a regulatory one."
```

```
[T26] CUSTOMER | thoughtful:3 | normal | mid | normal
"Understood. That's the same in Sweden."
```

```
[T27] AGENT | reassuring:3 | normal | mid | normal
"Right. The important part is that the retained records will be anonymized where the regulation allows. So instead of holding Henrik Lindqvist paid forty-nine dollars on this date, the line item becomes Customer ID nine-three-five paid forty-nine dollars on this date — the identifying link is broken to the extent the law permits."
```

```
[T28] CUSTOMER | satisfied:3 | normal | mid | normal
"That's a reasonable distinction. I can accept that."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Category three is the audio recording of any past support calls you made to us — those have a ninety-day retention regardless, so most of yours will age out naturally. Anything still in the ninety-day window gets included in the deletion."
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"Including this call?"
```

```
[T31] AGENT | reassuring:3 | normal | mid | normal
"This call is processed under the same rule — ninety days from today, then auto-deleted unless you've explicitly asked us to include it in the broader erasure, in which case I add a note to the ticket. Would you like it included?"
```

```
[T32] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes, please."
```

```
[T33] AGENT | professional:3 | normal | mid | normal | (typing)
"Noted on the ticket. Now I'm opening the Data Deletion request and routing it to our Data Compliance Officer. Their team owns these end-to-end."
```

```
[T34] CUSTOMER | curious:2 | normal | mid | normal
"What's the SLA on confirmation?"
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"You will receive a written acknowledgement of the request within seventy-two hours, with the case reference number. The actual deletion of category one and category three data is completed within thirty days of that acknowledgement. You'll receive a second written confirmation when deletion is complete. Both go to the email address on the closed account, so make sure that mailbox is still active for the next forty days."
```

```
[T36] CUSTOMER | thoughtful:3 | normal | mid | normal
"It's active. I'll keep it active until I see the second email."
```

```
[T37] AGENT | warm:3 | normal | mid | normal
"That's the right approach."
```

```
[T38] CUSTOMER | curious:3 | normal | mid | normal
"And after deletion — if I ever wanted to be a NexaLink customer again in the future, what happens then?"
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"You'd be onboarded as a brand-new customer with a brand-new account. The retained billing record under your anonymized Customer ID isn't linked back to a new sign-up, so you'd start fresh. No carry-over of prior service history, good or bad."
```

```
[T40] CUSTOMER | satisfied:3 | normal | mid | normal
"That's a clean answer. Thank you."
```

```
[T41] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you requested deletion of personal data on the closed account, I've opened a Data Deletion ticket routed to the Data Compliance Officer, you'll receive a seventy-two hour written acknowledgement, full deletion of non-essential and call-recording data within thirty days, and the legally retained billing records will be anonymized to the extent the law allows. Today's call is included in the deletion. Does that all sound correct?"
```

```
[T42] CUSTOMER | grateful:3 | normal | mid | normal
"Yes. That's exactly what I needed."
```

```
[T43] AGENT | warm:3 | normal | mid | normal
"You're welcome. I want to also say — the way you came in with the framing already clear made this very efficient. Most data deletion calls are slower because we have to walk customers through what their actual rights are first."
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Mr. Lindqvist?"
```

```
[T45] CUSTOMER | satisfied:3 | normal | mid | normal
"No, that's all. Thank you, Aisha."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is N-X-L dash one-seven-five-zero-zero-one-eight. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Take care."
```
