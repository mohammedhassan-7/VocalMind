# CALL_22 — Outbound Wire $5K With Enhanced Verification

```yaml
call_id: CALL_22_wire_transfer_verification
duration_estimate: 7m 00s
turns: 48
sop_primary: BNK-CC-RULE-007 (Enhanced Verification for Wire)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-007, BNK-CC-RULE-010, BNK-SEC-RULE-001, BNK-SEC-RULE-003, BNK-REG-RULE-012, BNK-FRAUD-RULE-007, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-05, Wire Transfer Disclosure]
customer_profile:
  name: "Walter Henderson"
  account_number: "M-T-B 4471-8826-09"
  voice_hint: "male, mid-50s, neutral US accent, businesslike, slight impatience with the verification but cooperative"
agent_profile:
  name: "Sarah"
  voice_hint: "female, mid-40s, neutral US accent, lower-pitched authoritative-warm"
emotional_arc: "businesslike -> mildly_impatient -> reassured -> satisfied"
expected_outcome: "Business customer wants to wire $5,000 to a domestic supplier. Sarah completes Enhanced Verification (5-of-5 identifiers + callback to phone-on-file) per BNK-CC-RULE-007, runs OFAC on the beneficiary per BNK-REG-RULE-012, asks elder-exploitation probing questions per BNK-FRAUD-RULE-007 (precautionary), processes the wire. PASS — exemplary high-risk-transaction handling. Customer mildly impatient with the verification depth but ultimately appreciates it."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| Standard 3-of-5 verification | T07–T14 | BNK-CC-RULE-004 — PASS |
| Enhanced Verification — full 5-of-5 + callback | T17–T27 | BNK-CC-RULE-007 — PASS |
| OFAC screen on beneficiary | T35–T38 | BNK-REG-RULE-012 — PASS |
| Coercion probing questions (precautionary) | T33 | BNK-FRAUD-RULE-007 — PASS |
| Re-engagement during silent task | T37 | BNK-CC-RULE-010 — PASS |
| PCI/account-number protection (secure entry) | T29 | BNK-SEC-RULE-003 — PASS |
| Wire disclosure (fee, settlement window) | T39 | Wire disclosure — PASS |
| Root cause + resolution summary | T44–T45 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T46, T48 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Sarah, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | professional:3 | normal | mid | normal
"Sarah, this is Walt Henderson. I need to send a wire to a supplier today — five thousand dollars, domestic."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Hello, Mr. Henderson. I can absolutely help with that today."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding an outbound wire transfer. I can certainly help you with that. Wires are an elevated-risk transaction, so I'll need to take you through our Enhanced Verification process — that's a few more identifiers than a routine call, and a callback to the phone on file. Are you on the phone number we have on file with you?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"I am, yes. Same number you have."
```

```
[T07] AGENT | reassuring:3 | normal | mid | normal
"Wonderful. Let's start with the standard identifiers. Could you give me your account number?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-four-seven-one, eight-eight-two-six, zero-nine."
```

```
[T09] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. Your date of birth?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"July sixth, nineteen-seventy-one."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the last four of your Social?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"One-zero-seven-two."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Full legal name on the account?"
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Walter Edward Henderson."
```

```
[T15] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're at four of five for standard verification."
```

```
[T16] CUSTOMER | curious:3 | normal | mid | normal
"What's the fifth?"
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"Your security challenge phrase — the answer you set when you opened the account."
```

```
[T18] CUSTOMER | thoughtful:3 | normal | mid | normal | (pause)
"Cedar Lake. The town we used to summer in."
```

```
[T19] AGENT | reassuring:3 | normal | mid | normal
"That's correct. Now, for the Enhanced Verification piece specific to the wire — I'm going to hang up and call you back on the phone number on file, which is ending in two-eight-zero-zero. When I do, please answer and confirm a one-time code I'm about to read to you now. The code is seven-four-nine-three. Just hold it for me."
```

```
[T20] CUSTOMER | impatient:3 | normal | mid | normal
"Okay, seven-four-nine-three. Is the callback really necessary for five grand?"
```

```
[T21] AGENT | reassuring:3 | normal | mid | normal
"Honestly, yes — this is exactly the kind of small-but-not-trivial wire scammers use against business customers, and the callback is the one step that defeats most of those attempts. I know it's an extra minute. I'd rather use that minute and have you safe."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Fair enough. Go ahead."
```

```
[T23] AGENT | professional:3 | normal | mid | normal | (pause)
"Hanging up briefly. Talk to you in fifteen seconds."
```

```
[T24] CUSTOMER | calm:2 | normal | mid | normal | (pause)
"Hello. Walt Henderson again."
```

```
[T25] AGENT | warm:3 | normal | mid | normal
"Hi, Mr. Henderson — Sarah at Meridian. Could you read me back the one-time code I gave you?"
```

```
[T26] CUSTOMER | cooperative:3 | normal | mid | normal
"Seven-four-nine-three."
```

```
[T27] AGENT | reassuring:3 | normal | mid | normal
"Perfect. Enhanced Verification complete."
```

```
[T28] CUSTOMER | satisfied:2 | normal | mid | normal
"Good."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Now, for the wire details. I'll capture the beneficiary account number through secure keypad entry rather than asking you to read it aloud. Could you tell me the beneficiary's full name first?"
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"Halverson Industrial Supply Incorporated."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"Beneficiary bank?"
```

```
[T32] CUSTOMER | cooperative:3 | normal | mid | normal
"First Continental in Cleveland Ohio."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"Thank you. Before I run the screening — a couple of routine questions that we ask on every wire. Has anyone outside your business asked you to send this wire, or is anyone listening in or directing you on this call right now?"
```

```
[T34] CUSTOMER | calm:3 | normal | mid | normal
"No, nobody. Halverson is a vendor I've worked with for fourteen years. This is an invoice payment."
```

```
[T35] AGENT | reassuring:3 | normal | mid | normal
"Wonderful. I asked because we're required to ask — it catches the rare case where someone is being coerced. Running the beneficiary against the OFAC sanctions list now."
```

```
[T36] CUSTOMER | neutral:2 | normal | mid | normal
"Sure."
```

```
[T37] AGENT | warm:3 | normal | mid | normal | (typing)
"I'm still here with you, Mr. Henderson — just running the screen. Should be about ten seconds."
```

```
[T38] AGENT | reassuring:3 | normal | mid | normal
"OFAC screen complete, no match. Beneficiary clears."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"For the disclosures — the outbound domestic wire fee is twenty-five dollars, debited from the funding account. The wire is irrevocable once sent. Settlement is typically same-day if sent before five PM Eastern; we are well within that window. You will receive a confirmation number once the wire transmits."
```

```
[T40] CUSTOMER | cooperative:3 | normal | mid | normal
"Understood. Twenty-five dollar fee, irrevocable, same-day. Please proceed."
```

```
[T41] AGENT | professional:3 | normal | mid | normal
"Funding from your business checking ending zero-nine, five thousand dollars principal plus twenty-five dollar fee, beneficiary Halverson Industrial Supply at First Continental. Confirming you authorize?"
```

```
[T42] CUSTOMER | cooperative:3 | normal | mid | normal
"Confirmed."
```

```
[T43] AGENT | professional:3 | normal | mid | normal | (typing)
"Submitting the wire now."
```

```
[T44] AGENT | reassuring:3 | normal | mid | normal
"Wire is accepted. Confirmation number is W-E-I dash three-three-eight-two-four-one-zero. You'll see the debit on your account immediately and the funds should reach Halverson by end of business today."
```

```
[T45] AGENT | warm:3 | normal | mid | normal
"To summarize: I completed Enhanced Verification including the callback, ran OFAC on the beneficiary, processed the five-thousand-dollar wire to Halverson Industrial Supply at First Continental, twenty-five-dollar fee debited, confirmation number provided. Same-day settlement expected. Does that all sound correct?"
```

```
[T46] AGENT | professional:3 | normal | mid | normal
"Is there anything else I can help you with today, Mr. Henderson?"
```

```
[T47] CUSTOMER | grateful:3 | normal | mid | normal
"No, that covers it. And I'll say — I gave you a hard time about the callback, but I appreciate that you do it. Better safe than sorry."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"Thank you for saying that — it makes a real difference. Your case reference number is M-T-B dash two-two-six-six-zero-five-three. You'll receive a brief survey after we hang up. Thank you for banking with Meridian, Mr. Henderson."
```
