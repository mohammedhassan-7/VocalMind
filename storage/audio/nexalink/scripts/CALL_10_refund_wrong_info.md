# CALL_10 — Refund Request With Misquoted Policy Information

```yaml
call_id: CALL_10_refund_wrong_info
duration_estimate: 5m 45s
turns: 40
sop_primary: SOP-01 (Refund Request Processing)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-011, FIN-RULE-001, FIN-RULE-002, FIN-RULE-004, FIN-RULE-010, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.1 - Billing Concepts, Section 3.3 - Compensation Matrix]
customer_profile:
  name: "Kevin Maldonado"
  account_number: "4729-8801-13"
  voice_hint: "male, 30s, slight East-Coast accent, sceptical and informed"
agent_profile:
  name: "Daniel"
  voice_hint: "male, late 20s, neutral US accent, professional but inexperienced"
emotional_arc: "frustrated -> confused -> sceptical -> resigned"
expected_outcome: "Customer requests a credit for a ~6-hour outage (under 24h, ineligible per FIN-RULE-001). Daniel CORRECTLY denies a credit but does so by quoting INCORRECT figures: he states the threshold is '12 hours' instead of 24, claims the agent cap is '$150' instead of $200, and FABRICATES the refund timeline from memory rather than using the approved script (FIN-RULE-010 FAIL). Customer leaves resigned but with wrong expectations. Multiple wrong-information failures, no forbidden phrases."
content_warning: "Agent provides incorrect policy figures and a fabricated refund timeline."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + PIN — PASS |
| A.C.E.S. light, partial Acknowledge | T15 | CS-RULE-011 — MINOR (no real empathy) |
| WRONG INFO — quotes 12 hr outage threshold | T19 | FIN-RULE-001 actual is 24 hr — FAIL (factual error) |
| Eligibility denial correct in outcome | T21 | FIN-RULE-001/FIN-RULE-002 — PASS in result, FAIL in reasoning |
| WRONG INFO — states cap is "$150" | T27 | FIN-RULE-004 actual is $200 — FAIL (factual error) |
| WRONG INFO — fabricates refund timeline from memory | T32 | FIN-RULE-010 — FAIL (timeline quoted is not the approved script) |
| Resolution summary | T35 | CS-RULE-019 — PASS |
| Anything else + case ref + survey | T37, T39 | CS-RULE-020, CS-RULE-021 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Daniel. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"This call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | frustrated:3 | normal | mid | normal
"This is Kevin Maldonado. My internet was down for like six hours last Tuesday and I want a credit on my bill for it."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Got it, Mr. Maldonado. Let me see what I can do."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling regarding an outage credit, and I can certainly look into that for you. Before I pull up the account I need to verify a few details — could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-seven-two-nine, eight-eight-zero-one, one-three."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thanks. Last four of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Three-three-zero-eight."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"And your security PIN?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Five-five-four-seven."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"That matches. You're verified."
```

```
[T12] CUSTOMER | neutral:2 | normal | mid | normal
"Good."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Now, what time did the outage start and when did it come back?"
```

```
[T14] CUSTOMER | frustrated:3 | normal | mid | normal
"Started around ten in the morning Tuesday, came back maybe four in the afternoon. So six hours, give or take. I had work calls — it was a real problem."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"Okay. Let me check the network log for your area."
```

```
[T16] CUSTOMER | neutral:2 | normal | mid | normal
"Alright."
```

```
[T17] AGENT | professional:3 | normal | mid | normal | (typing)
"Yes — I can see a regional incident in your service area, it ran from nine forty-eight AM to about three fifty-two PM. That's confirmed as a real outage."
```

```
[T18] CUSTOMER | vindicated:2 | normal | mid | normal
"Right, so that lines up. Can I get a credit?"
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"So here's the thing — our compensation policy only kicks in for outages that exceed twelve hours. Yours was just over six. Under the twelve-hour line there's no automatic credit."
```

```
[T20] CUSTOMER | confused:3 | normal | mid | normal
"Wait, twelve hours? I thought it was twenty-four."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"It's twelve under the current policy. So unfortunately for a six hour outage you don't qualify for a financial credit. I'm sorry about that."
```

```
[T22] CUSTOMER | skeptical:3 | normal | mid | normal
"That doesn't sound right, but okay. Is there nothing you can do?"
```

```
[T23] AGENT | thoughtful:3 | normal | mid | normal
"I mean, I can apply a small goodwill credit. Not a refund of the day, just a courtesy gesture."
```

```
[T24] CUSTOMER | curious:3 | normal | mid | normal
"How much are we talking?"
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"I can do up to ten dollars on a goodwill credit for something like this."
```

```
[T26] CUSTOMER | frustrated:3 | normal | mid | normal
"Ten dollars. For six hours of no internet during a work day. That's it?"
```

```
[T27] AGENT | apologetic:3 | normal | mid | normal
"My agent cap on a single call is one hundred and fifty dollars total, but the matrix for a sub-threshold outage tops out at ten. That's all I'm able to authorize myself for this situation."
```

```
[T28] CUSTOMER | resigned:3 | normal | mid | normal
"Fine. Apply the ten."
```

```
[T29] AGENT | professional:3 | normal | mid | normal | (typing)
"Applying a ten dollar courtesy credit now."
```

```
[T30] AGENT | reassuring:3 | normal | mid | normal
"Done. Ten dollar goodwill credit posted to your account."
```

```
[T31] CUSTOMER | curious:3 | normal | mid | normal
"When does that show up?"
```

```
[T32] AGENT | thoughtful:3 | normal | mid | normal
"For a courtesy credit it usually posts within two to three business days, and then it'll show up on your next bill or the one after that."
```

```
[T33] CUSTOMER | skeptical:3 | normal | mid | normal
"Two to three business days, and then maybe the bill after the next one?"
```

```
[T34] AGENT | professional:3 | normal | mid | normal
"Roughly, yeah. Sometimes a little faster if the cycle's about to close."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"To summarize: you reported a six hour outage Tuesday, I confirmed it on the network log. Because it was under the threshold I couldn't apply a service credit, but I did apply a ten dollar goodwill credit. It'll show on your next bill or the one after."
```

```
[T36] CUSTOMER | resigned:3 | normal | mid | normal
"Yeah. Got it."
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"Is there anything else I can help you with today, Mr. Maldonado?"
```

```
[T38] CUSTOMER | curt:3 | normal | mid | normal
"No, that's all."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"Your case reference number is N-X-L dash one-zero-five-seven-three-three-eight. You'll receive a brief survey after we hang up — appreciate the feedback if you have time."
```

```
[T40] AGENT | professional:3 | normal | mid | normal
"Thank you for being a NexaLink customer, Mr. Maldonado. Have a good rest of your day."
```
