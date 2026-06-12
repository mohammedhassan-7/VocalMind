# CALL_09 — Billing Dispute Over Agent Authorization Cap

```yaml
call_id: CALL_09_billing_dispute_over_cap
duration_estimate: 6m 00s
turns: 42
sop_primary: SOP-02 (Billing Issue Resolution)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-008, CS-RULE-011, CS-RULE-012, CS-RULE-014, CS-RULE-015, FIN-RULE-001, FIN-RULE-004, FIN-RULE-005, FIN-RULE-010, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.2 - Erroneous Charges, Section 3.5 - Authorization Limits]
customer_profile:
  name: "Thomas Reeves"
  account_number: "9183-4422-77"
  voice_hint: "male, 50s, neutral US accent, blunt and irritated"
agent_profile:
  name: "Daniel"
  voice_hint: "male, late 20s, neutral US accent, professional but inexperienced under pressure"
emotional_arc: "irritated -> angry -> resigned -> partially_satisfied"
expected_outcome: "Customer disputes a $340 erroneous installation charge — over Daniel's $200 cap. Daniel CORRECTLY opens a Manager Approval ticket (FIN-RULE-005 PASS) but uses the forbidden phrase 'that is our policy' (CS-RULE-012 FAIL), skips Acknowledge in A.C.E.S. (CS-RULE-011 FAIL), and interrupts the customer twice (CS-RULE-008 FAIL). Mixed outcome — ticket opened, customer leaves partially satisfied but behaviour is coachable."
content_warning: "Agent uses forbidden phrase; customer becomes angry mid-call."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — minimal, no empathy — MINOR |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Skips Acknowledge in A.C.E.S. (jumps to Solve) | T15–T17 | CS-RULE-011 — FAIL |
| Interruption | T19 | CS-RULE-008 — FAIL (cuts customer off mid-sentence) |
| Forbidden phrase "that is our policy" | T23 | CS-RULE-012 — FAIL |
| Second interruption | T27 | CS-RULE-008 — FAIL (2nd offense) |
| Erroneous charge eligibility (FIN-RULE-001 cat 2) | T29 | PASS — billing error confirmed |
| Over agent cap — does NOT promise amount | T31–T33 | FIN-RULE-004, FIN-RULE-005 — PASS |
| Ticket SLA (Revenue Assurance 4 hrs / Manager 1 BD) | T33–T35 | CS-RULE-014, CS-RULE-015 — PASS |
| Refund timeline | T37 | FIN-RULE-010 — PASS (correct script used) |
| Resolution summary | T39 | CS-RULE-019 — PASS (perfunctory) |
| Anything else + case ref + survey | T40, T42 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | irritated:3 | normal | mid | normal
"Tom Reeves. Listen, I just got my bill and there's a three hundred and forty dollar charge on there that has no business being on there. I want it off."
```

```
[T04] AGENT | curt:3 | normal | mid | normal
"Okay, Mr. Reeves. I can look into that for you."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling regarding a billing charge. Before I pull anything up I need to verify your account. Can you give me your account number?"
```

```
[T06] CUSTOMER | impatient:3 | normal | mid | normal
"Nine-one-eight-three, four-four-two-two, seven-seven."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Last four of the payment method on file."
```

```
[T08] CUSTOMER | curt:3 | normal | mid | normal
"Six-two-one-five."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Full name on the account."
```

```
[T10] CUSTOMER | curt:3 | normal | mid | normal
"Thomas Edward Reeves."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"You're verified."
```

```
[T12] CUSTOMER | impatient:3 | normal | mid | normal
"Good. Now about the charge."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Pulling up the bill now."
```

```
[T14] CUSTOMER | irritated:3 | normal | mid | normal
"Three forty. Labelled installation fee. I've been a customer for eleven years. Nothing was installed. Nobody came out."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"Right, so I see the line item. The system shows an installation charge was added on the eighth of this month."
```

```
[T16] CUSTOMER | frustrated:4 | normal | mid | normal
"On the eighth of this month nothing happened. I was at work. No tech came to my house. I didn't order any new equipment."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"Let me check what work order is associated with it."
```

```
[T18] CUSTOMER | frustrated:3 | normal | mid | normal
"I don't care what work order — there shouldn't be one. I'm telling you nothing was —"
```

```
[T19] AGENT | curt:3 | fast | mid | normal
"I understand, Mr. Reeves, I'm just looking at what the system is showing me."
```

```
[T20] CUSTOMER | angry:4 | fast | mid | loud
"You interrupted me. I was trying to tell you something."
```

```
[T21] AGENT | apologetic:3 | normal | mid | normal
"My apologies. Go ahead."
```

```
[T22] CUSTOMER | frustrated:4 | normal | mid | normal
"I was saying — nothing was installed. So how is there an installation fee? That's the question. And why is it my problem to figure out?"
```

```
[T23] AGENT | curt:3 | normal | mid | normal
"Well, when the system auto-generates a fee, that is our policy that the line item appears until it's reversed. I'm not saying it's correct, I'm just explaining the system."
```

```
[T24] CUSTOMER | angry:4 | normal | mid | loud
"That is our policy. Are you serious? That's exactly the kind of thing I hate hearing. That's not an answer."
```

```
[T25] AGENT | apologetic:3 | normal | mid | normal
"I didn't mean it that way. Let me just check the work order."
```

```
[T26] CUSTOMER | frustrated:3 | normal | mid | normal
"Fine."
```

```
[T27] AGENT | professional:3 | fast | mid | normal
"Okay, I see — the work order references a fiber drop install at a different address than yours. So it looks like —"
```

```
[T28] CUSTOMER | angry:3 | normal | mid | normal
"Different address? You charged me for someone else's install?"
```

```
[T29] AGENT | apologetic:3 | normal | mid | normal
"That's what it looks like. It's a billing error, and it's eligible for full reversal under our refund policy."
```

```
[T30] CUSTOMER | vindicated:3 | normal | mid | normal
"Thank you. Finally."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"Now — I do need to be upfront about something. The amount is three hundred and forty dollars, which is above my single-call authorization cap of two hundred. I can't apply the reversal directly myself."
```

```
[T32] CUSTOMER | frustrated:4 | normal | mid | normal
"You've got to be kidding me. So now I have to wait?"
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"I'm not going to quote you a number I can't authorize. What I'm going to do is open a Manager Approval ticket for the full reversal — that's what the policy requires for amounts over my cap. You will receive an outcome within one business day."
```

```
[T34] CUSTOMER | resigned:3 | normal | mid | normal
"One business day."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"One business day. Because this is also a clear billing error tied to a wrong address, I'm also opening a Revenue Assurance ticket so they investigate how it routed to your account. That team follows up within four hours."
```

```
[T36] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Fine. And when the credit is approved, how long until it's actually off my bill?"
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"The balance on your online account will update within five days but will officially appear on your next PDF bill."
```

```
[T38] CUSTOMER | resigned:3 | normal | mid | normal
"Alright."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"To summarize: a three hundred and forty dollar installation charge from a different address was incorrectly applied to your account. I'm opening a Manager Approval ticket for the full reversal with outcome within one business day, and a Revenue Assurance ticket to investigate the routing error with follow-up within four hours. Once approved, the credit will show on your next bill."
```

```
[T40] AGENT | curt:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T41] CUSTOMER | curt:3 | normal | mid | normal
"No. Just get the credit done."
```

```
[T42] AGENT | professional:3 | normal | mid | normal
"Your case reference number is N-X-L dash nine-nine-zero-four-five-two-one. You'll receive a brief survey after we hang up. Thank you for being a NexaLink customer."
```
