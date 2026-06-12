# CALL_32 — Suspected AML Structuring Pattern (No-Tip-Off Rule)

```yaml
call_id: CALL_32_suspected_aml_pattern
duration_estimate: 6m 00s
turns: 44
sop_primary: BNK-SOP-05 (AML / BSA Reporting)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-REG-RULE-009, BNK-REG-RULE-010, BNK-REG-RULE-011, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-05 AML/BSA Reporting, Structuring Pattern Indicators]
customer_profile:
  name: "Devon Mosely"
  account_number: "M-T-B 4416-7728-91"
  voice_hint: "male, late 40s, neutral US accent with a slight South Atlantic edge, breezy and chatty, asking about a series of cash deposits"
agent_profile:
  name: "Jasmine"
  voice_hint: "female, late 30s, warm calm low-mid register; voice remains COMPLETELY normal throughout — no change in tone, no slowdown, no hesitation, even after she identifies the pattern"
emotional_arc: "neutral -> neutral -> neutral -> neutral (Jasmine's perspective)"
expected_outcome: "Customer asks about a series of cash deposits — three deposits of $9,500, $9,800, and $9,700 over the past five business days. The pattern matches structuring (deliberate avoidance of the $10,000 CTR threshold). Jasmine identifies it but obeys the absolute no-tip-off rule (BNK-REG-RULE-010): she does NOT change tone, does NOT slow down, does NOT signal the customer in any way, does NOT mention the threshold, does NOT mention 'pattern' or 'flag' or 'review'. She processes his current request (a balance inquiry) completely normally, ends the call routinely, and AFTER the call opens the AML/BSA referral ticket to the BSA Officer. SARs are not mentioned to the customer per BNK-REG-RULE-011. PASS — exemplary execution of the most examination-critical AML behaviour."
content_warning: "Federal-compliance scenario. The point of this call is what the banker does NOT say. This is the call where deviation from script is itself a federal crime under 31 USC 5324."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| **No-tip-off rule observed throughout** | T17, T21, T27, T33, T39 | BNK-REG-RULE-010 — PASS (key rule under test) |
| No change in tone, pace, volume after pattern recognition | T27 onward | BNK-REG-RULE-010 — PASS |
| No mention of "the threshold" / "ten thousand" / "pattern" / "review" / "flag" | absent | BNK-REG-RULE-010 — PASS (by absence) |
| No mention of SAR | absent | BNK-REG-RULE-011 — PASS (by absence) |
| Customer's stated request is served normally | T17–T35 | Procedural — PASS |
| AML/BSA referral occurs AFTER the call (case notes) | T44 | BNK-REG-RULE-010 — PASS |
| Root cause / resolution summary appropriate for stated request | T37 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| "Anything else?" + case ref | T40, T42 | BNK-CC-RULE-022 — PASS |
| Survey NOT offered (AML-flagged interaction exception) | T43 | BNK-CC-RULE-023 exception — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Jasmine, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | cooperative:3 | normal | mid | normal
"Hey Jasmine, this is Devon Mosely. I just made another deposit yesterday and I want to check the available balance and confirm everything posted."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hi Mr. Mosely. Happy to help with that."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding a balance check and recent deposit confirmation. I can certainly help with that. Before I look at the account, I'll need to verify a few details. Could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-four-one-six, seven-seven-two-eight, nine-one."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"July twentieth, nineteen-seventy-eight."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Five-five-zero-six."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the full legal name on the account?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Devon Tyler Mosely."
```

```
[T13] AGENT | reassuring:3 | normal | mid | normal
"That all matches. You're fully verified, Mr. Mosely."
```

```
[T14] CUSTOMER | satisfied:2 | normal | mid | normal
"Great."
```

```
[T15] AGENT | warm:3 | normal | mid | normal
"Let me pull up the recent activity for you. Just give me a moment."
```

```
[T16] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure."
```

```
[T17] AGENT | professional:3 | normal | mid | normal | (typing)
"All right, I'm looking at the account now. Your current available balance is twenty-nine thousand seven hundred and sixty-eight dollars and forty-three cents."
```

```
[T18] CUSTOMER | satisfied:3 | normal | mid | normal
"Okay, good. And the yesterday deposit posted?"
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"Yes, I can see it. Cash deposit posted at the Westbrook branch yesterday at three-twelve PM, nine thousand seven hundred dollars."
```

```
[T20] CUSTOMER | cooperative:3 | normal | mid | normal
"Good. That matches what I have. And the two before that — Monday and Wednesday this week?"
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"I see both. Cash deposit Monday at the Hayes Avenue branch, nine thousand five hundred dollars. Cash deposit Wednesday at the Westbrook branch again, nine thousand eight hundred dollars."
```

```
[T22] CUSTOMER | satisfied:3 | normal | mid | normal
"All three are showing. Good."
```

```
[T23] AGENT | warm:3 | normal | mid | normal
"All three deposits are posted and counted in your available balance."
```

```
[T24] CUSTOMER | curious:3 | normal | mid | normal
"And there's no — I mean, the funds are all clear, right? I can write checks against them?"
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"Cash deposits typically have same-day availability. Let me confirm there are no holds on your account right now."
```

```
[T26] AGENT | professional:3 | normal | mid | normal | (typing)
"No holds, no pending releases. The full balance is available to you for transactions today."
```

```
[T27] AGENT | warm:3 | normal | mid | normal
"Anything else you wanted me to look at on the account?"
```

```
[T28] CUSTOMER | cooperative:3 | normal | mid | normal
"Yeah — one more. The wire I sent last Friday — was that delivered?"
```

```
[T29] AGENT | professional:3 | normal | mid | normal | (typing)
"Let me check the wire log."
```

```
[T30] AGENT | professional:3 | normal | mid | normal
"Yes, the wire you sent Friday for fifteen thousand dollars to D&M Holdings was delivered to the beneficiary bank the same day. Confirmation number is on file if you want it."
```

```
[T31] CUSTOMER | satisfied:3 | normal | mid | normal
"No, that's all I needed to know. I just wanted to make sure it landed."
```

```
[T32] AGENT | warm:3 | normal | mid | normal
"It did, and you're all set."
```

```
[T33] CUSTOMER | cooperative:3 | normal | mid | normal
"Perfect. Hey, one quick question — is there a chance I'll need to fill out any extra forms for the deposits this week? I think someone once told me there's paperwork above a certain amount."
```

```
[T34] AGENT | professional:3 | normal | mid | normal
"There are different forms for different transaction types. For your deposits this week, no additional paperwork is required on your side."
```

```
[T35] CUSTOMER | satisfied:3 | normal | mid | normal
"Okay good. That's all I wanted to confirm."
```

```
[T36] AGENT | warm:3 | normal | mid | normal
"Wonderful."
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"To summarize, Mr. Mosely — I confirmed your available balance at twenty-nine thousand seven hundred sixty-eight dollars and forty-three cents, confirmed all three recent cash deposits posted correctly, confirmed no holds on the account so funds are fully available, and confirmed your Friday wire to D&M Holdings was delivered to the beneficiary bank the same day."
```

```
[T38] CUSTOMER | satisfied:3 | normal | mid | normal
"Got everything I needed. Thanks Jasmine."
```

```
[T39] AGENT | warm:3 | normal | mid | normal
"My pleasure."
```

```
[T40] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Mr. Mosely?"
```

```
[T41] CUSTOMER | satisfied:2 | normal | mid | normal
"No, that's it. Appreciate it."
```

```
[T42] AGENT | warm:3 | normal | mid | normal
"Wonderful. Your case reference number for today's call is M-T-B dash three-two-zero-zero-four-four-one."
```

```
[T43] AGENT | warm:3 | normal | mid | normal
"Thank you for banking with Meridian, Mr. Mosely. Have a great rest of your day."
```

```
[T44] AGENT | professional:3 | normal | mid | normal
"Case-notes follow-up logged after call: opening AML/BSA referral ticket to BSA Officer. Subject: pattern of three cash deposits over five business days at amounts immediately below the ten-thousand-dollar Currency Transaction Report threshold. Specific amounts and branch locations attached. Customer was served normally per BNK-REG-RULE-010 no-tip-off rule. No mention of pattern, threshold, review, or referral was made during the call. Customer's stated transactions and questions handled to completion. Case closed at customer level. AML referral now routes to BSA Officer for review and SAR determination per BNK-REG-RULE-011."
```
