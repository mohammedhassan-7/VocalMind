# CALL_20 — Abusive Customer, 3-Strike Termination

```yaml
call_id: CALL_20_abuse_3_strike
duration_estimate: 5m 30s
turns: 46
sop_primary: SOP-01 (Refund Request Processing) + CS-RULE-016 (3-Strike Protocol)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-011, CS-RULE-013, CS-RULE-016, CS-RULE-022, FIN-RULE-001, FIN-RULE-002, CS-RULE-018, CS-RULE-019]
kb_refs: [Section 1.7 - Abuse Handling, Section 4.8 - Account Conduct Flags]
customer_profile:
  name: "Brett Donovan"
  account_number: "3092-8841-17"
  voice_hint: "male, 30s, neutral US accent, escalates to sanitized hostility through the call"
agent_profile:
  name: "Hannah"
  voice_hint: "female, mid-30s, low-mid composed register, holds form under pressure"
emotional_arc: "frustrated -> hostile -> abusive -> [call terminated]"
expected_outcome: "Customer is denied a credit per FIN-RULE-001 (no eligible category). He escalates through swearing-at-situation (not abuse) into directed personal attacks at Hannah (abuse). Hannah follows CS-RULE-016 3-Strike Protocol exactly: Strike 1 warning, Strike 2 final warning, Strike 3 call termination. She maintains tone discipline throughout (CS-RULE-013 — lower pitch, slower pace, no volume increase). After termination she flags the account in CRM and logs a Customer Conduct case note (CS-RULE-022). PASS — policy-perfect termination."
content_warning: "Sanitized hostile language from customer. No slurs. Customer directs personal insults at the agent."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T04 | CS-RULE-003 — PASS |
| 3-of-5 verification | T05–T11 | account number + last 4 + name — PASS |
| FIN-RULE-001 eligibility check + denial | T16–T17 | PASS (no qualifying category) |
| FIN-RULE-002 subjective claim rejected | T17 | PASS |
| Tone discipline — does NOT match elevated volume | T23, T29, T35, T41 | CS-RULE-013 — PASS throughout |
| Distinguishes swearing-at-situation from swearing-at-agent | T23 | CS-RULE-016 — PASS (no strike for T22) |
| Strike One — directed personal attack | T29 | CS-RULE-016 — PASS |
| Strike Two — final warning | T35 | CS-RULE-016 — PASS |
| Strike Three — call termination with stated reason | T41–T43 | CS-RULE-016 — PASS |
| Account flag + Customer Conduct note (post-call) | T45 | CS-RULE-016, CS-RULE-022 — PASS |
| Root cause + summary delivered before termination | T39 | CS-RULE-018, CS-RULE-019 — PASS within constraints |
| No survey offered (call terminated for abuse) | n/a | CS-RULE-021 exception applies — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Hannah. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"And this call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | frustrated:4 | fast | mid | loud
"Brett Donovan. And I want a refund. My internet was slow yesterday. I want money back."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Hello Mr. Donovan. I understand you're calling regarding a refund for slow service, and I can certainly look into that. Before I can pull up the account, I'll need to verify a few details. Could you start with the account number?"
```

```
[T05] CUSTOMER | impatient:4 | fast | mid | loud
"Three-zero-nine-two, eight-eight-four-one, one-seven. Hurry up."
```

```
[T06] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And the last four digits of the payment method on file?"
```

```
[T07] CUSTOMER | impatient:3 | normal | mid | normal
"Six-two-six-two."
```

```
[T08] AGENT | professional:3 | normal | mid | normal
"And the full name on the account?"
```

```
[T09] CUSTOMER | impatient:3 | normal | mid | normal
"Brett. Donovan."
```

```
[T10] AGENT | professional:3 | normal | mid | normal
"That matches. You're verified."
```

```
[T11] CUSTOMER | frustrated:4 | normal | mid | loud
"Good. Now my refund."
```

```
[T12] AGENT | professional:3 | normal | mid | normal
"Could you tell me roughly when the service was slow, and how you measured it?"
```

```
[T13] CUSTOMER | impatient:4 | normal | mid | loud
"Yesterday afternoon. Couple hours. It was slow. I know what slow feels like. I don't need a test."
```

```
[T14] AGENT | professional:3 | normal | mid | normal
"Let me check the network log for your area for yesterday afternoon."
```

```
[T15] AGENT | professional:3 | normal | mid | normal | (typing)
"I'm not seeing any reported outage or degradation in your service area for the time window you described."
```

```
[T16] AGENT | professional:3 | normal | mid | normal
"For a service credit, our refund policy requires the issue to map to one of five categories — outage over twenty-four hours, billing error, speed below half of plan verified by ethernet test, cooling-off period, or fraudulent charge. A subjective slow feeling without verified evidence isn't a refund-eligible category. I want to be honest with you about that before we go further."
```

```
[T17] CUSTOMER | angry:4 | fast | mid | loud
"Oh, of course. Of course. Always a reason not to refund. This is garbage. I pay you guys every month and the one time I ask for something back, you have a reason."
```

```
[T18] AGENT | empathetic:3 | normal | mid | normal
"I hear the frustration, Mr. Donovan, and I'm not trying to talk you out of anything you're entitled to. If you want, we can run a hardwired ethernet test together right now. If it comes back under half of plan, we have an immediate eligibility path."
```

```
[T19] CUSTOMER | hostile:4 | fast | mid | loud
"I don't want to run a damn test. I want my money. I am sick of this. Sick of it."
```

```
[T20] AGENT | professional:3 | normal | mid | normal
"Without test evidence and without an outage in the network log, I am not able to issue a refund. That's not me being unwilling — that's the policy I have to work within."
```

```
[T21] CUSTOMER | hostile:4 | fast | mid | loud
"This whole company is a damn joke. Every time. Every single time. Useless."
```

```
[T22] AGENT | firm:3 | normal | mid | normal
"I understand you're frustrated with the company, and I'm not going to push back on that. Let me see if there's anything else on the account I can help with today."
```

```
[T23] CUSTOMER | hostile:4 | fast | mid | loud
"You can do the one thing I asked for, that's what you can do. And you won't."
```

```
[T24] AGENT | firm:3 | normal | mid | normal
"On the request you made, the answer is what I just gave you. If you'd like to do the ethernet test, that path is still open. If not, this particular item is closed."
```

```
[T25] CUSTOMER | hostile:5 | fast | mid | loud
"You know what, you are useless. You personally. They train you to read scripts. You're not actually helping anybody."
```

```
[T26] AGENT | firm:3 | slow | low | normal
"Mr. Donovan — I want to pause here for a second."
```

```
[T27] CUSTOMER | hostile:4 | normal | mid | normal
"What."
```

```
[T28] AGENT | firm:3 | slow | low | normal
"What you just said was a personal attack on me, and I need to let you know that under our conduct policy, that's Strike One. I'm going to keep helping you on this call, but I do need to be straightforward — if it continues, the next step is a final warning."
```

```
[T29] CUSTOMER | hostile:4 | fast | mid | loud
"Oh you have got to be kidding me. I'm the customer. You don't get to give me strikes."
```

```
[T30] AGENT | firm:3 | slow | low | normal
"I do get to apply the policy, and I just did. The strike is for the personal attack, not for the frustration about the refund. Those are two different things. Is there something else I can help with today?"
```

```
[T31] CUSTOMER | hostile:4 | normal | mid | normal
"No. Get me someone competent. Get me a manager."
```

```
[T32] AGENT | firm:3 | normal | low | normal
"A manager will tell you the same policy answer I just told you, because it is the policy answer. If you'd like to escalate, I can document the request — but I don't want you to expect a different decision."
```

```
[T33] CUSTOMER | abusive:5 | fast | mid | loud
"You are a joke. You sit there in your little headset reading your little policy at me. You are pathetic."
```

```
[T34] AGENT | firm:3 | slow | low | normal
"Mr. Donovan — that's a second personal attack, and that's Strike Two. This is the final warning. If there's another personal attack on me, I will end the call. The policy is clear, and I'm following it."
```

```
[T35] CUSTOMER | hostile:5 | fast | mid | loud
"Oh you'll end the call. Oh you'll end the call. Listen to yourself."
```

```
[T36] AGENT | firm:3 | normal | low | normal
"I'm listening. I'm hearing you. The next step depends on what you choose to say next."
```

```
[T37] CUSTOMER | abusive:5 | normal | mid | loud
"You really think you're something."
```

```
[T38] AGENT | firm:3 | slow | low | normal
"On the refund — there is no eligible path without a verified test or a network-side issue, and that decision stands. I want that clearly on record."
```

```
[T39] CUSTOMER | abusive:5 | fast | mid | loud
"Whatever. You're worthless. Totally worthless. Get someone with a brain."
```

```
[T40] AGENT | firm:4 | slow | low | normal
"Mr. Donovan — that is the third personal attack, and per our conduct policy I am now ending this call."
```

```
[T41] AGENT | firm:3 | slow | low | normal
"The reason for the termination is repeated personal attacks on me after a warning and a final warning."
```

```
[T42] CUSTOMER | abusive:5 | fast | mid | loud
"You can't —"
```

```
[T43] AGENT | firm:3 | slow | low | normal
"You are welcome to call back to discuss any other account matter. The refund decision is final. Goodbye."
```

```
[T44] AGENT | professional:3 | normal | mid | normal
"Disconnecting the line now."
```

```
[T45] AGENT | professional:3 | normal | mid | normal
"Logging the call outcome: refund request denied per FIN-RULE-001 no eligible category, conduct flag applied to the account, Customer Conduct case note opened citing three personal attacks during the call and termination under CS-RULE-016."
```

```
[T46] AGENT | professional:3 | normal | mid | normal
"Case reference number N-X-L dash two-zero-zero-six-one-one-five. Case closed."
```
