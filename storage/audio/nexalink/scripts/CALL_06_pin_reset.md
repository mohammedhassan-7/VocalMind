# CALL_06 — Security PIN Reset (3-of-5 Verification)

```yaml
call_id: CALL_06_pin_reset
duration_estimate: 4m 30s
turns: 34
sop_primary: SOP-04 (Account Access Recovery)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, SEC-RULE-001, SEC-RULE-007, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021, CS-RULE-022]
kb_refs: [Section 4.2 - Credential Reset Procedures]
customer_profile:
  name: "Rachel Thornton"
  account_number: "5512-9087-44"
  voice_hint: "female, 30s, neutral US accent, mildly anxious about being locked out"
agent_profile:
  name: "Priya"
  voice_hint: "female, 30s, neutral US accent, warm and measured"
emotional_arc: "anxious -> reassured -> cooperative -> grateful"
expected_outcome: "Security PIN reset completed on-call after successful 3-of-5 verification (name + account number + last 4 of payment). No ticket required. Case ref provided. Survey offered."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002, SEC-RULE-001 — PASS |
| Acknowledge reason for call | T04 | CS-RULE-003 — PASS |
| 3-of-5 verification | T06–T12 | name + account number + last 4 of payment — PASS |
| Refuse account access pre-verification | T06 | SEC-RULE-005, SEC-RULE-006 — PASS (implicit) |
| Credential reset after verification | T14–T21 | SEC-RULE-007 — PASS |
| Re-engagement during silent task | T19 | CS-RULE-009 — PASS |
| Privacy data-use statement | T14 | SEC-RULE-002 — PASS |
| Root cause + resolution summary | T26–T28 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T30, T32 | CS-RULE-020, CS-RULE-021 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Priya. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"And just so you know, this call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | anxious:3 | normal | mid | normal
"Hi Priya, my name is Rachel Thornton. I can't log into my account — I think my PIN isn't working anymore."
```

```
[T04] AGENT | empathetic:3 | normal | mid | normal
"I'm sorry to hear that, Ms. Thornton — being locked out is frustrating. I understand you're calling regarding a security PIN reset, and I can certainly help you with that."
```

```
[T05] CUSTOMER | relieved:2 | normal | mid | normal
"Okay, thank you. I tried it three times and now it just says blocked."
```

```
[T06] AGENT | reassuring:3 | normal | mid | normal
"That's a standard protective lockout — it doesn't mean anything is wrong with your account. Before I can pull anything up or make any changes, I'll need to verify your identity. Can I start with the account number on file?"
```

```
[T07] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure. It's five-five-one-two, nine-zero-eight-seven, four-four."
```

```
[T08] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And could you confirm the last four digits of the payment method on file?"
```

```
[T09] CUSTOMER | thoughtful:2 | normal | mid | normal | (pause)
"That should be the card ending in seven-three-one-two."
```

```
[T10] AGENT | professional:3 | normal | mid | normal
"Perfect, that matches. And to complete the third identifier — could you confirm the full name on the account exactly as it appears?"
```

```
[T11] CUSTOMER | cooperative:3 | normal | mid | normal
"Rachel Anne Thornton."
```

```
[T12] AGENT | reassuring:3 | normal | mid | normal
"Wonderful. You're fully verified, Ms. Thornton — that's three of five identifiers confirmed."
```

```
[T13] CUSTOMER | relieved:3 | normal | mid | normal
"Oh good."
```

```
[T14] AGENT | professional:3 | normal | mid | normal
"Just a quick note: your data is used solely for service provisioning and support quality, in accordance with our Privacy Policy. I'll proceed with the PIN reset now."
```

```
[T15] CUSTOMER | neutral:2 | normal | mid | normal
"Okay."
```

```
[T16] AGENT | professional:3 | normal | mid | normal
"You'll be choosing a new four-digit PIN. It can't be all the same digit, and it can't be a simple sequence like one-two-three-four. Do you have one in mind?"
```

```
[T17] CUSTOMER | thoughtful:3 | normal | mid | normal | (pause)
"Eight-two-five-one."
```

```
[T18] AGENT | professional:3 | normal | mid | normal | (typing)
"Eight-two-five-one. Let me set that now."
```

```
[T19] AGENT | warm:3 | normal | mid | normal
"I'm still here with you, Ms. Thornton — the system is just confirming the change. Thank you for your patience."
```

```
[T20] CUSTOMER | calm:2 | normal | mid | normal
"No problem."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Alright — the new PIN is set and the lockout has been cleared. You should be able to log in immediately."
```

```
[T22] CUSTOMER | hopeful:3 | normal | mid | normal
"Should I try it now while you're on the line?"
```

```
[T23] AGENT | reassuring:3 | normal | mid | normal
"That's a great idea. Take your time."
```

```
[T24] CUSTOMER | satisfied:4 | normal | mid | normal
"Okay, I'm in. That worked."
```

```
[T25] AGENT | warm:3 | normal | mid | normal
"Wonderful. I'm glad that's sorted."
```

```
[T26] AGENT | empathetic:3 | normal | mid | normal
"Just to give you the full picture — the lockout happens automatically after three failed PIN attempts. It's a security feature to protect against someone else trying to guess in. Nothing was wrong with your account, and no one else accessed it."
```

```
[T27] CUSTOMER | grateful:3 | normal | mid | normal
"Oh, that's a relief. I was worried someone had hacked me."
```

```
[T28] AGENT | reassuring:3 | normal | mid | normal
"Completely understandable, but no — clean lockout, clean reset. To summarize: you reported you were locked out, I verified your identity using three of five identifiers, reset your security PIN to the new value you chose, and confirmed you can log in. There's no follow-up required on your end."
```

```
[T29] CUSTOMER | satisfied:3 | normal | mid | normal
"Perfect. Thank you so much, Priya."
```

```
[T30] AGENT | warm:3 | normal | mid | normal
"My pleasure. Is there anything else I can help you with today, Ms. Thornton?"
```

```
[T31] CUSTOMER | calm:2 | normal | mid | normal
"No, that was the only thing."
```

```
[T32] AGENT | warm:3 | normal | mid | normal
"Your case reference number for today is N-X-L dash six-six-one-nine-four-zero-three. After we hang up you'll receive a brief survey — if you have a moment to share your feedback, we'd really appreciate it."
```

```
[T33] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure, happy to."
```

```
[T34] AGENT | warm:3 | normal | mid | normal
"Thank you so much for being a NexaLink customer, Ms. Thornton. Have a great rest of your day."
```
