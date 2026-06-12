# CALL_15 — Two-Factor Authentication Recovery

```yaml
call_id: CALL_15_2fa_recovery
duration_estimate: 6m 15s
turns: 46
sop_primary: SOP-04 (Account Access Recovery)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, SEC-RULE-001, SEC-RULE-002, SEC-RULE-007, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021, CS-RULE-022]
kb_refs: [Section 4.3 - Multi-Factor Authentication, Section 4.6 - Authenticator App Reset]
customer_profile:
  name: "Emma Caraway"
  account_number: "1908-7762-43"
  voice_hint: "female, late 20s, neutral US accent, mildly stressed about being locked out before a deadline"
agent_profile:
  name: "Aisha"
  voice_hint: "female, late 30s, warm low-mid register, deliberate and reassuring"
emotional_arc: "anxious -> reassured -> cooperative -> grateful"
expected_outcome: "Customer lost the phone with her authenticator app and cannot complete two-factor sign-in. Aisha completes full 3-of-5 verification, removes the old 2FA enrollment, walks the customer through enrolling a fresh authenticator on her new phone, and confirms login. PASS — SOP-04 + SEC-RULE-007 satisfied on-call (no store visit required because the customer cleared phone-based verification). No ticket required. Case ref + survey provided."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002, SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Privacy data-use statement | T15 | SEC-RULE-002 — PASS |
| Credential reset after verification | T19–T35 | SEC-RULE-007 — PASS (on-phone completion, customer cleared 3-of-5) |
| A.C.E.S. — Empathize + Solve | T04, T17 | CS-RULE-011 — PASS |
| Re-engagement during silent task | T31 | CS-RULE-009 — PASS |
| Root cause + resolution summary | T41–T43 | CS-RULE-018, CS-RULE-019 — PASS |
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
[T03] CUSTOMER | anxious:4 | normal | mid | normal
"Hi Aisha, I'm Emma Caraway. I'm in a bit of a panic — my phone was stolen yesterday, I got a new one this morning, and now I can't get into my account because the two-factor codes are still going to the old phone."
```

```
[T04] AGENT | empathetic:4 | normal | mid | normal
"Oh, Emma, I'm so sorry that happened. Losing your phone is stressful enough without being locked out of accounts on top of it. Take a breath — this is absolutely something I can sort out with you on this call."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a two-factor authentication recovery, and I can certainly help you with that. Before I touch anything on the account, I'll need to verify your identity. Could you start with the account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. One-nine-zero-eight, seven-seven-six-two, four-three."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And could you confirm the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | thoughtful:2 | normal | mid | normal
"Last four are three-three-eight-four."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And to complete a third identifier — could you confirm the full name on the account, exactly as it appears?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Emma Lillian Caraway."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified, Emma."
```

```
[T12] CUSTOMER | relieved:3 | normal | mid | normal
"Oh, thank you."
```

```
[T13] AGENT | warm:3 | normal | mid | normal
"You're welcome. Now I want to walk you through what we're going to do, before we do it, so nothing comes as a surprise."
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"Your data is used solely for service provisioning and support quality, in accordance with our Privacy Policy. Because you've cleared identity verification by phone, I can complete the two-factor reset on this call — you won't need to visit a store. I'll remove the old authenticator enrollment from your account, and then together we'll set up a fresh enrollment on your new phone."
```

```
[T16] CUSTOMER | hopeful:3 | normal | mid | normal
"That would be amazing. Thank you."
```

```
[T17] AGENT | empathetic:3 | normal | mid | normal
"Of course. Before I unenroll the old one — do you have the new phone in your hand right now? And do you have an authenticator app already, or would you like a recommendation?"
```

```
[T18] CUSTOMER | cooperative:3 | normal | mid | normal
"I have the new phone, yes. I don't have an authenticator app yet — what do you recommend?"
```

```
[T19] AGENT | reassuring:3 | normal | mid | normal
"Either Google Authenticator or Microsoft Authenticator will work, and they're both free. Whichever you prefer. They behave identically for our setup, so just go with what feels natural."
```

```
[T20] CUSTOMER | thoughtful:3 | normal | mid | normal
"I'll grab Google Authenticator. Installing it now."
```

```
[T21] AGENT | warm:3 | normal | mid | normal
"Take your time. There's no rush at all."
```

```
[T22] CUSTOMER | concentrating:3 | normal | mid | normal | (pause)
"Okay, it's installed and open. It's asking me to scan a code or enter a setup key."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Perfect — that's exactly the screen we want. I'm going to unenroll the old phone now and generate a fresh setup key for your account. One moment."
```

```
[T24] AGENT | professional:3 | normal | mid | normal | (typing)
"Removing the old enrollment."
```

```
[T25] AGENT | reassuring:3 | normal | mid | normal
"Done. The old phone can no longer generate valid codes for your account, which is what you want given that it's no longer in your possession."
```

```
[T26] CUSTOMER | relieved:3 | normal | mid | normal
"Oh, that's such a relief."
```

```
[T27] AGENT | warm:3 | normal | mid | normal
"I thought you'd feel that way. Now generating a fresh enrollment for the new phone."
```

```
[T28] AGENT | professional:3 | normal | mid | normal | (typing)
"Okay. I have a setup key ready. I'm going to read it to you in groups of four characters — type each group into the authenticator app's setup key field exactly as I say it, lowercase letters and digits as I read them."
```

```
[T29] CUSTOMER | concentrating:2 | normal | mid | normal
"Okay, ready."
```

```
[T30] AGENT | professional:3 | normal | mid | normal
"Group one: x-seven-q-m. Group two: r-two-n-p. Group three: t-eight-f-j. Group four: w-five-k-d."
```

```
[T31] AGENT | warm:3 | normal | mid | normal
"I'm still here with you, Emma — just take your time typing those in. Let me know when you've got all four groups."
```

```
[T32] CUSTOMER | concentrating:3 | normal | mid | normal | (pause)
"Okay, all four are in. It's showing me a six-digit code now."
```

```
[T33] AGENT | reassuring:3 | normal | mid | normal
"Perfect — that means the enrollment is connected. Read me the six digits showing right now so I can verify the pairing on my side."
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-one-eight, seven-two-six."
```

```
[T35] AGENT | professional:3 | normal | mid | normal | (typing)
"And matched. The new phone is officially your two-factor device."
```

```
[T36] CUSTOMER | grateful:4 | normal | mid | normal
"Oh, thank you so much."
```

```
[T37] AGENT | warm:3 | normal | mid | normal
"Would you like to try logging into your account right now while we're on the line, just so we both know it works?"
```

```
[T38] CUSTOMER | hopeful:3 | normal | mid | normal
"Yes, please."
```

```
[T39] CUSTOMER | satisfied:4 | normal | mid | normal | (pause)
"Okay — username, password, it asked for the code, I put in the current code, and… I'm in. It worked."
```

```
[T40] AGENT | warm:3 | normal | mid | normal
"That's exactly what we wanted to see. You're fully set up."
```

```
[T41] AGENT | empathetic:3 | normal | mid | normal
"And just to give you the broader picture — the issue here wasn't anything wrong with your account. The old phone simply had the only valid two-factor secret, and once it was gone, only a manual reset like the one we just did could restore access. That's by design — it's what keeps your account safe."
```

```
[T42] CUSTOMER | satisfied:3 | normal | mid | normal
"That makes sense. I'm relieved it wasn't more complicated."
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported your authenticator was on a phone that was stolen, I verified your identity using three of five identifiers, removed the old two-factor enrollment, walked you through enrolling a fresh authenticator on the new phone, and confirmed you can log in. No follow-up is required on your end. Does that all sound right?"
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Emma?"
```

```
[T45] CUSTOMER | grateful:3 | normal | mid | normal
"No, that's all. Honestly, thank you for being so calm about it — you really helped."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"That's what I'm here for. Your case reference number is N-X-L dash one-five-five-zero-nine-one-two. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Take care, Emma."
```
