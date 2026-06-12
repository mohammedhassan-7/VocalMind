# CALL_08 — Cooling-Off Cancellation (Within 14 Days)

```yaml
call_id: CALL_08_cooling_off
duration_estimate: 5m 00s
turns: 36
sop_primary: SOP-05 (Customer Retention / Cancellation)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, FIN-RULE-009, FIN-RULE-010, CS-RULE-011, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 5.1 - Cooling-Off Period, Section 5.4 - Equipment Returns]
customer_profile:
  name: "Diane Ortega"
  account_number: "3367-5510-08"
  voice_hint: "female, 50s, neutral US accent, polite but firm on her decision"
agent_profile:
  name: "Priya"
  voice_hint: "female, 30s, neutral US accent, warm and measured"
emotional_arc: "apologetic_firm -> respected -> reassured -> grateful"
expected_outcome: "Cooling-off cancellation processed at agent's seat (FIN-RULE-009 — no ticket). Equipment return label emailed. Full refund of contract deposit confirmed. Survey not offered per CS-RULE-021 cancellation exception."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | account number + last 4 of payment + full name — PASS |
| A.C.E.S. light retention attempt | T16–T20 | CS-RULE-011 — PASS (respects customer's decision after one offer) |
| Cooling-off refund at agent's seat | T22–T27 | FIN-RULE-009 — PASS (no ticket required) |
| Refund timeline verbatim | T28 | FIN-RULE-010 — PASS (card reversal script) |
| Equipment return logistics | T29–T31 | Section 5.4 — PASS |
| Root cause acknowledgement + summary | T32–T33 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref, NO survey | T35, T36 | CS-RULE-020, CS-RULE-021 cancellation exception — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Priya. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"And this call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | firm:3 | normal | mid | normal
"This is Diane Ortega. I signed up about a week and a half ago and I need to cancel the service."
```

```
[T04] AGENT | empathetic:3 | normal | mid | normal
"Hello, Ms. Ortega. I'm sorry to hear that, and of course I can help."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling regarding a cancellation, and I can certainly help you with that. Before I make any changes, I'll need to verify a few details — could you start with your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Three-three-six-seven, five-five-one-zero, zero-eight."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"Four-four-eight-one."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And the full name on the account?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Diane Marie Ortega."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"You're fully verified, Ms. Ortega. I can see your account was activated nine days ago — so you're well inside our fourteen-day cooling-off window."
```

```
[T12] CUSTOMER | firm:2 | normal | mid | normal
"Good. That's what I thought."
```

```
[T13] AGENT | empathetic:3 | normal | mid | normal
"Before I process anything — would you mind sharing what's prompting the cancellation? I won't push back on your decision, but it helps us improve."
```

```
[T14] CUSTOMER | firm:3 | normal | mid | normal
"Honestly, the speed isn't there. I tested it on ethernet like the installer suggested and I'm getting maybe forty megabits on a two-hundred plan. And I just don't want to deal with troubleshooting — I'd rather go back to my old provider."
```

```
[T15] AGENT | concerned:3 | normal | mid | normal
"That's well below what you signed up for, and I'm sorry the install didn't land the way it should have."
```

```
[T16] AGENT | thoughtful:3 | normal | mid | normal
"I can absolutely process the cooling-off cancellation. I do want to offer one thing first, only because you mentioned the speed issue — if you'd like, we could send a tech out tomorrow to check the line, and if it can't be fixed I'll cancel right then. But if you'd rather just close out today, that's completely your call."
```

```
[T17] CUSTOMER | firm:3 | normal | mid | normal
"No, I appreciate that, but I've made my decision. I want to cancel."
```

```
[T18] AGENT | reassuring:3 | normal | mid | normal
"Of course. Cancelling today."
```

```
[T19] CUSTOMER | grateful:2 | normal | mid | normal
"Thank you for not making it a fight."
```

```
[T20] AGENT | warm:3 | normal | mid | normal
"It's your service and your decision — that's how it should be."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"So under our cooling-off policy, because you're within the fourteen-day window, this is a full no-questions-asked refund. There's no early termination fee, and the initial deposit and first month's charge will be reversed in full."
```

```
[T22] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay, good."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"I'm seeing a charge of one hundred and forty-nine dollars on the card ending in four-four-eight-one — that covers the eighty-nine dollar deposit and the sixty dollar pro-rated first month. I'll be reversing the full one forty-nine."
```

```
[T24] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes."
```

```
[T25] AGENT | professional:3 | normal | mid | normal | (typing)
"Processing the cancellation and refund now."
```

```
[T26] AGENT | reassuring:3 | normal | mid | normal
"The account is closed effective today, and the refund has been submitted."
```

```
[T27] CUSTOMER | curious:3 | normal | mid | normal
"How long before I see the money back?"
```

```
[T28] AGENT | professional:3 | normal | mid | normal
"We have processed the refund today, but depending on your bank it may take one to two billing cycles to appear."
```

```
[T29] CUSTOMER | neutral:2 | normal | mid | normal
"Okay."
```

```
[T30] AGENT | professional:3 | normal | mid | normal
"For the equipment — I'll email you a prepaid return label within the next hour. Just pack the modem, the router, and the power adapter in the original box if you still have it, drop it at any carrier location, and you're done. As long as it arrives back in good condition there's nothing more on your end."
```

```
[T31] CUSTOMER | satisfied:3 | normal | mid | normal
"That's easy enough."
```

```
[T32] AGENT | empathetic:3 | normal | mid | normal
"And I do want to acknowledge — the speed you described, forty on a two-hundred plan, that's a real issue and I'm sorry the install didn't go better. If you ever want to give us another try in the future, you're more than welcome."
```

```
[T33] AGENT | reassuring:3 | normal | mid | normal
"To summarize: I cancelled your account today under our cooling-off policy, reversed the full one hundred forty-nine dollar charge to your card ending in four-four-eight-one, and the equipment return label is on its way to your email. Does that all sound correct?"
```

```
[T34] CUSTOMER | grateful:3 | normal | mid | normal
"Yes. Thank you, Priya. You made that very painless."
```

```
[T35] AGENT | warm:3 | normal | mid | normal
"You're very welcome. Is there anything else I can help you with today, Ms. Ortega?"
```

```
[T36] AGENT | warm:3 | normal | mid | normal
"Your case reference number is N-X-L dash eight-eight-three-one-zero-four-seven. Thank you for giving NexaLink a try, Ms. Ortega — take care."
```
