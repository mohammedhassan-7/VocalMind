# CALL_24 — Overdraft Fees Dispute Over Authorization Cap

```yaml
call_id: CALL_24_overdraft_dispute_over_cap
duration_estimate: 6m 30s
turns: 46
sop_primary: BNK-SOP-04-adj (Fee Waiver within Authority)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-009, BNK-CC-RULE-012, BNK-CC-RULE-013, BNK-CC-RULE-015, BNK-CC-RULE-016, BNK-SEC-RULE-001, BNK-FIN-RULE-001, BNK-FIN-RULE-002, BNK-FIN-RULE-003, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [Overdraft Fee Waiver Matrix]
customer_profile:
  name: "Raymond Castillo"
  account_number: "M-T-B 3318-0094-22"
  voice_hint: "male, mid-40s, neutral US accent, frustrated father trying to figure out cascading fees"
agent_profile:
  name: "Tyler"
  voice_hint: "male, late 20s, neutral US accent, professional but inexperienced under pressure"
emotional_arc: "frustrated -> angry -> resigned -> partially_satisfied"
expected_outcome: "Customer disputes $385 across five overdraft fees triggered by one timing issue with a deposit. Total over Tyler's $250 cap. Tyler CORRECTLY opens a Manager Approval ticket per BNK-FIN-RULE-002 (no amount promised). BUT he uses the forbidden phrase 'that's our policy' (BNK-CC-RULE-013 FAIL), skips Empathize in A.C.E.S. (BNK-CC-RULE-012 FAIL), and interrupts the customer once (BNK-CC-RULE-009 MINOR). Mixed outcome — ticket opened correctly, behaviour coachable."
content_warning: "Agent uses forbidden phrase; customer becomes angry mid-call."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — minimal — MINOR |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| Skips Empathize in A.C.E.S. (jumps to defend the fees) | T17, T19 | BNK-CC-RULE-012 — FAIL |
| Forbidden phrase "that's our policy" | T23 | BNK-CC-RULE-013 — FAIL |
| Interruption mid-sentence | T29 | BNK-CC-RULE-009 — MINOR FAIL |
| BNK-FIN-RULE-003 180-day check performed | T27 | PASS (none in window) |
| Over agent cap — does NOT promise amount | T33, T35 | BNK-FIN-RULE-001, BNK-FIN-RULE-002 — PASS |
| Manager Approval ticket SLA (1 BD) | T35, T37 | BNK-CC-RULE-015, BNK-CC-RULE-016 — PASS |
| Root cause + resolution summary | T42–T43 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T44, T46 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Tyler, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"This call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | frustrated:4 | fast | mid | normal
"Ray Castillo. I just looked at my account and there are five overdraft fees on there for seventy-seven bucks each. Three hundred eighty-five dollars in fees in one day."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Okay Mr. Castillo. Let me take a look at that."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling about overdraft fees. I'll need to verify the account first — could you give me your account number?"
```

```
[T06] CUSTOMER | impatient:3 | fast | mid | normal
"Three-three-one-eight, zero-zero-nine-four, two-two."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth?"
```

```
[T08] CUSTOMER | curt:3 | normal | mid | normal
"April second, nineteen-seventy-nine."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social?"
```

```
[T10] CUSTOMER | curt:3 | normal | mid | normal
"Four-zero-one-eight."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the full legal name on the account?"
```

```
[T12] CUSTOMER | curt:3 | normal | mid | normal
"Raymond Diego Castillo."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"You're verified."
```

```
[T14] CUSTOMER | frustrated:4 | normal | mid | normal
"Good. Now. Five overdraft fees. In one day. Three eighty-five. Explain."
```

```
[T15] AGENT | professional:3 | normal | mid | normal | (typing)
"Looking at the activity."
```

```
[T16] AGENT | professional:3 | normal | mid | normal
"I see five debits posted Tuesday morning that overdrafted the account. Auto pay for the car, mortgage, gym, two utility companies — they all came in at once."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"And your direct deposit for the paycheck hit Tuesday afternoon. So the debits posted before the credit, and each of the five items triggered an overdraft fee of seventy-seven dollars."
```

```
[T18] CUSTOMER | angry:4 | fast | mid | loud
"Right, that's exactly what happened. My paycheck was already there by lunchtime — I checked. I just got hit by your processing order. I have been a customer here for nine years and this is the first time anything like this has happened."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"I understand."
```

```
[T20] CUSTOMER | frustrated:4 | normal | mid | normal
"Do you? Because three hundred eighty-five dollars in fees in one day is not okay. That's more than the mortgage payment that the overdraft is on."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Let me see what waiver options apply."
```

```
[T22] CUSTOMER | impatient:3 | normal | mid | normal
"Please."
```

```
[T23] AGENT | curt:3 | normal | mid | normal
"So debits posting before credits in the same business day — that's our policy on processing order, and the fees are technically valid when that happens. But there is a waiver mechanism for cases like yours."
```

```
[T24] CUSTOMER | angry:4 | normal | mid | loud
"That's our policy. That's literally the worst answer you could have given me. I am telling you the money was there and you charged me three hundred eighty-five dollars in fees, and your answer is that's our policy?"
```

```
[T25] AGENT | apologetic:3 | normal | mid | normal
"That came out wrong, Mr. Castillo. What I meant is the order in which debits and credits post is a known system behaviour. I was about to say that for cases like yours we do have a waiver — let me focus on that part."
```

```
[T26] CUSTOMER | frustrated:3 | normal | mid | normal
"Then focus on that part."
```

```
[T27] AGENT | professional:3 | normal | mid | normal | (typing)
"Looking at your fee history first. Our policy is one courtesy fee waiver per account per one hundred eighty days. You have not had any courtesy waivers on this account in that window."
```

```
[T28] CUSTOMER | curious:3 | normal | mid | normal
"So I qualify for the waiver."
```

```
[T29] AGENT | professional:3 | fast | mid | normal
"You qualify for the courtesy mechanism. The question is the amount. My single-call authorization cap is two hundred fifty dollars in fee waivers per transaction. Your total —"
```

```
[T30] CUSTOMER | frustrated:4 | normal | mid | normal
"Wait, you're going to waive only two hundred fifty of the three eighty-five?"
```

```
[T31] AGENT | apologetic:3 | normal | mid | normal
"Sorry, let me finish — I'm not telling you the outcome. I'm telling you what's mine to authorize versus what needs to go to a manager."
```

```
[T32] CUSTOMER | curt:3 | normal | mid | normal
"Go ahead."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"The total is three hundred eighty-five dollars, which is over my cap. I am not going to quote you a refund amount I can't authorize myself, because that wouldn't be fair to you if Manager Approval came back with something different."
```

```
[T34] CUSTOMER | resigned:3 | normal | mid | normal
"So what's the actual path."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"I'm going to open a Manager Approval ticket for the full three hundred eighty-five dollar reversal, with all five fees documented and the timing of your direct deposit attached as evidence. Manager Approval returns a decision within one business day. They will call the number on file."
```

```
[T36] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"One business day. Okay."
```

```
[T37] AGENT | professional:3 | normal | mid | normal | (typing)
"Opening the ticket now. Given that you have no prior courtesy waivers in the last six months and the timing was unfavourable rather than your error, the expected outcome is favourable — but again, the decision is theirs."
```

```
[T38] CUSTOMER | resigned:3 | normal | mid | normal
"Fine."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"In the meantime, if you want to avoid this happening again — we do have a free overdraft transfer service that links to a savings or another deposit account. If a debit would overdraft, the system pulls automatically from the linked account instead of charging the fee. I can set that up on this call if you'd like."
```

```
[T40] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. Please. Link my savings ending six-five-eight-three."
```

```
[T41] AGENT | professional:3 | normal | mid | normal | (typing)
"Overdraft transfer linked. Twelve-dollar transfer fee per occurrence, which is much less than the seventy-seven-dollar overdraft fee. That's active immediately."
```

```
[T42] AGENT | professional:3 | normal | mid | normal
"Just to give you the full picture — what happened is that on Tuesday, five debits processed before your paycheck credit landed. The system applied a seventy-seven dollar overdraft fee on each of the five debits, totalling three eighty-five. Manager Approval will rule on the waiver within one business day, and going forward the overdraft transfer link will protect you."
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"To summarize: I opened a Manager Approval ticket for the full three hundred eighty-five dollar fee reversal, decision within one business day. I linked your savings ending six-five-eight-three for overdraft transfer protection going forward. The expected outcome on the ticket is favourable but the decision is theirs. Does that all sound right?"
```

```
[T44] AGENT | professional:3 | normal | mid | normal
"Is there anything else I can help you with today, Mr. Castillo?"
```

```
[T45] CUSTOMER | curt:3 | normal | mid | normal
"No. Just get the waiver approved."
```

```
[T46] AGENT | professional:3 | normal | mid | normal
"Your case reference number is M-T-B dash two-four-zero-zero-nine-three-eight. You'll receive a brief survey after we hang up. Thank you for being a Meridian customer, Mr. Castillo."
```
