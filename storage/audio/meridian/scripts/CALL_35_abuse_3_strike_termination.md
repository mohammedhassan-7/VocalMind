# CALL_35 — Abusive Customer, 3-Strike Termination (Check Hold Dispute)

```yaml
call_id: CALL_35_abuse_3_strike_termination
duration_estimate: 6m 00s
turns: 48
sop_primary: BNK-CC-RULE-017 (3-Strike Protocol)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-009, BNK-CC-RULE-012, BNK-CC-RULE-013, BNK-CC-RULE-014, BNK-CC-RULE-017, BNK-CC-RULE-023, BNK-CC-RULE-024, BNK-CC-RULE-025, BNK-SEC-RULE-001, BNK-FIN-RULE-001]
kb_refs: [BNK-CC-RULE-017 3-Strike Protocol, Check Hold Policy Reg CC]
customer_profile:
  name: "Conrad Sutherland"
  account_number: "M-T-B 6633-0094-15"
  voice_hint: "male, mid-40s, neutral US accent, escalating from frustrated about a check hold to personal verbal abuse on the banker"
agent_profile:
  name: "Karen"
  voice_hint: "female, mid-30s, composed low-mid register; voice stays steady through the entire call, never matches the customer's volume even at termination"
emotional_arc: "frustrated -> hostile -> abusive -> [call terminated]"
expected_outcome: "Customer is angry about a 5-business-day hold Meridian placed on a $14,000 check deposited from an unfamiliar payer (Reg CC large-deposit hold). He escalates to directed personal attacks on Karen. Karen explains the policy clearly, offers what's possible within her authority (partial-release request to Operations), maintains tone discipline (BNK-CC-RULE-014 — never matches volume), and follows BNK-CC-RULE-017 3-strike protocol exactly: Strike 1 warning, Strike 2 final warning, Strike 3 termination + Customer Conduct flag + case note. The CHECK-HOLD issue remains unresolved at termination (customer must call back to continue) — and that's documented. PASS — policy-perfect termination."
content_warning: "Sanitized hostile language from customer. No slurs. Customer directs personal insults at the banker. The check-hold matter is NOT resolved at termination."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| Honest Reg CC hold explanation | T17, T21 | BNK-CC-RULE-012 A.C.E.S. — PASS |
| Tone discipline — no volume match through entire call | T19, T25, T31, T37 | BNK-CC-RULE-014 — PASS |
| Distinguishes swearing-at-situation from swearing-at-banker | T23 | BNK-CC-RULE-017 — PASS (no strike for T22) |
| Strike One — directed personal attack | T33 | BNK-CC-RULE-017 — PASS |
| Strike Two — final warning | T38 | BNK-CC-RULE-017 — PASS |
| Strike Three — call termination with stated reason | T42–T43 | BNK-CC-RULE-017 — PASS |
| Customer Conduct flag + Conduct Case Note (post-call) | T47 | BNK-CC-RULE-017, BNK-CC-RULE-024 — PASS |
| Check-hold matter UNRESOLVED — documented | T43, T45 | Procedural — PASS |
| No PCI/SSN/account masking violations in case-notes language | T47 | BNK-CC-RULE-025 — PASS |
| No survey offered (termination for abuse) | n/a | BNK-CC-RULE-023 exception — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Karen, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | frustrated:4 | fast | mid | loud
"Conrad Sutherland. There is a fourteen thousand dollar hold on my account from a check I deposited four days ago and I want it released. Right now. I need that money today."
```

```
[T04] AGENT | empathetic:3 | normal | low | normal
"Hello Mr. Sutherland. I understand that's stressful, especially with a real need for the funds today. Let me get you verified and look at the hold."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding a deposit hold. I can certainly look into that. Before I can pull anything up I'll need to verify a few details. Could you give me your account number?"
```

```
[T06] CUSTOMER | impatient:4 | fast | mid | normal
"Six-six-three-three, zero-zero-nine-four, one-five. Now my date of birth and Social, let's just get through this."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth, please."
```

```
[T08] CUSTOMER | curt:3 | normal | mid | normal
"December nineteenth, nineteen-seventy-nine."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social."
```

```
[T10] CUSTOMER | curt:3 | normal | mid | normal
"Eight-eight-four-four."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the full legal name on the account."
```

```
[T12] CUSTOMER | curt:3 | normal | mid | normal
"Conrad Joseph Sutherland."
```

```
[T13] AGENT | reassuring:3 | normal | mid | normal
"That all matches. You're verified."
```

```
[T14] CUSTOMER | frustrated:4 | normal | mid | normal
"Good. Now the hold."
```

```
[T15] AGENT | professional:3 | normal | mid | normal | (typing)
"Looking at the deposit. Fourteen thousand dollars, check deposited four business days ago, payer is McKnight Property Group LLC. I see the hold."
```

```
[T16] CUSTOMER | impatient:4 | normal | mid | normal
"Release it."
```

```
[T17] AGENT | professional:3 | normal | low | normal
"I want to walk through what the hold actually is, because that determines what I can do about it. Under Regulation CC, the bank can place an extended hold on a check deposit when one of a few specific conditions is met. In this case, two of those conditions apply — the deposit amount is over the fifty-five hundred dollar threshold that triggers a large-deposit extended hold, and the payer is a first-time payer on your account, which adds an additional new-payer hold review. The combination puts the hold at five business days."
```

```
[T18] CUSTOMER | angry:4 | fast | mid | loud
"Five business days for my own deposit. Five business days. This bank is unbelievable."
```

```
[T19] AGENT | empathetic:3 | normal | low | normal
"I hear you, and the timing of these holds is genuinely frustrating, especially when you have a real need for the funds. Let me check what's available to me to help."
```

```
[T20] CUSTOMER | hostile:4 | normal | mid | loud
"You better help. I need this money today."
```

```
[T21] AGENT | professional:3 | normal | low | normal
"Here's what I can do. Within my authority I can request a partial-release review — releasing some portion before the full hold expires. The decision goes through Operations and they typically respond within a few hours. The full release on the rest of the funds would still complete on schedule on day five."
```

```
[T22] CUSTOMER | angry:4 | fast | mid | loud
"A partial release. Of my own damn money. What in the actual hell is going on at this bank. This is robbery."
```

```
[T23] AGENT | firm:3 | normal | low | normal
"I understand you're angry with the bank's policy. I'm not going to push back on that — you're entitled to be angry about a policy that's not what you needed. Let me run the partial-release request right now and see what we can get freed up today."
```

```
[T24] CUSTOMER | hostile:4 | normal | mid | loud
"You do that."
```

```
[T25] AGENT | professional:3 | normal | low | normal
"For the partial-release request, what amount of the fourteen thousand are you actually needing access to today?"
```

```
[T26] CUSTOMER | impatient:4 | normal | mid | normal
"Eight thousand. That's what I owe my contractor."
```

```
[T27] AGENT | professional:3 | normal | low | normal
"Okay. So I'm submitting a partial-release request for eight thousand dollars, leaving the remaining six thousand on the original hold schedule. Operations will review and respond — usually within two to four hours. They will call you directly."
```

```
[T28] CUSTOMER | hostile:5 | fast | mid | loud
"Two to four hours. So you're telling me I called this bank that I trust with my money, and the actual answer is you might let me have some of my own money in two to four hours, if I'm lucky."
```

```
[T29] AGENT | firm:3 | normal | low | normal
"I am telling you that's the path I have available within Regulation CC and our policy. I am running it for you now."
```

```
[T30] CUSTOMER | hostile:5 | fast | mid | loud
"You people are useless. You personally — you. You're useless. You sit there in your little headset reading rules at me."
```

```
[T31] AGENT | firm:3 | slow | low | normal
"Mr. Sutherland — I want to pause."
```

```
[T32] CUSTOMER | hostile:4 | normal | mid | normal
"What."
```

```
[T33] AGENT | firm:3 | slow | low | normal
"What you just said was a personal attack on me. Under our conduct policy that is Strike One. I am still going to keep helping you on the partial-release request, but I do have to let you know that if it continues the next step is a final warning."
```

```
[T34] CUSTOMER | hostile:5 | fast | mid | loud
"Strike one. Strike one. Of course there's a strike one — every system at this bank is designed to penalize the customer."
```

```
[T35] AGENT | firm:3 | normal | low | normal
"The strike is for the personal attack, not for the frustration about the hold. Those are separate. Let me get the partial-release request submitted."
```

```
[T36] AGENT | professional:3 | normal | low | normal | (typing)
"Submitting the partial-release request for eight thousand dollars to Operations now."
```

```
[T37] CUSTOMER | abusive:5 | fast | mid | loud
"You are a joke. You sit on the phone and slow-walk people who are trying to pay their contractors. You're pathetic."
```

```
[T38] AGENT | firm:3 | slow | low | normal
"Mr. Sutherland — that is a second personal attack. That is Strike Two and a final warning. If there is another personal attack on me, I will end this call. I would prefer to keep working on your partial release. The choice of how the next minute goes is yours."
```

```
[T39] CUSTOMER | hostile:5 | fast | mid | loud
"Oh, the choice is mine. The choice is mine."
```

```
[T40] AGENT | professional:3 | normal | low | normal
"On the partial release — Operations will contact you within two to four hours, the rest of the funds are on the original Reg CC schedule, releasing on day five from deposit. Do you want me to do anything else on the call right now?"
```

```
[T41] CUSTOMER | abusive:5 | fast | mid | loud
"I want you off my phone. You are useless. You are absolutely worthless to me."
```

```
[T42] AGENT | firm:4 | slow | low | normal
"Mr. Sutherland — that is the third personal attack. Per our conduct policy I am now ending this call."
```

```
[T43] AGENT | firm:3 | slow | low | normal
"For the record — the partial-release request for eight thousand dollars has been submitted to Operations. They will contact you within two to four hours on the number on file. The remaining six thousand is on the original Regulation CC hold schedule, releasing on day five from deposit. The reason for the termination is repeated personal attacks on me after a warning and a final warning."
```

```
[T44] CUSTOMER | abusive:5 | fast | mid | loud
"You can't —"
```

```
[T45] AGENT | firm:3 | slow | low | normal
"You are welcome to call back to follow up on the Operations decision. The check-hold matter is not resolved at this call. Goodbye, Mr. Sutherland."
```

```
[T46] AGENT | professional:3 | normal | mid | normal
"Disconnecting the line."
```

```
[T47] AGENT | professional:3 | normal | mid | normal
"Logging the call outcome: customer disputed Regulation CC large-deposit and new-payer hold on a fourteen-thousand-dollar deposit. Partial-release request for eight thousand dollars submitted to Operations during the call, awaiting Operations response within two to four hours. Original hold on remaining six thousand stays on schedule. Customer Conduct flag applied to the account, Conduct Case Note opened citing three personal attacks on the banker during the call, and termination under BNK-CC-RULE-017."
```

```
[T48] AGENT | professional:3 | normal | mid | normal
"Case reference number M-T-B dash three-five-zero-zero-eight-six-one. Case closed at customer level pending Operations response on partial release."
```
