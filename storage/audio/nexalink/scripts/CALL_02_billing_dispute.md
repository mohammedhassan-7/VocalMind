# CALL_02 — Billing Dispute (Two New Charges, No Escalation)

```yaml
call_id: CALL_02_billing_dispute
duration_estimate: 7m 00s
turns: 50
sop_primary: SOP-02 (Billing Issue Resolution)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-008, CS-RULE-011, CS-RULE-012, CS-RULE-014, CS-RULE-015, FIN-RULE-001, FIN-RULE-004, FIN-RULE-005, FIN-RULE-007, FIN-RULE-010, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.2 - Erroneous Charges, Section 3.5 - Authorization Limits]
customer_profile:
  name: "Linda Park"
  account_number: "5294-7710-38"
  voice_hint: "female, 50s, neutral US accent, sharp articulation, escalates from frustrated to angry"
agent_profile:
  name: "Daniel"
  voice_hint: "male, late 20s, neutral US accent, professional but shows pressure as the call escalates"
emotional_arc: "frustrated -> angry -> resigned -> partially_satisfied"
expected_outcome: "Linda Park calls disputing a $245 priority service fee she never authorized plus a $39 second add-on charge. Total disputed = $284, over Daniel's $200 cap. Daniel CORRECTLY opens a Manager Approval ticket per FIN-RULE-005 (no amount promised) AND a Revenue Assurance ticket since this is the customer's 4th refund request in 90 days (FIN-RULE-007 auto-flag). Daniel uses the forbidden phrase 'I don't know' once (CS-RULE-012 FAIL) and skips Empathize in A.C.E.S. (CS-RULE-011 partial FAIL). LOW performer behaviour with a mostly-correct ticket workflow."
content_warning: "Customer is angry; agent uses one forbidden phrase."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — minimal — MINOR |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Skips Empathize in A.C.E.S. (jumps to investigate) | T17 | CS-RULE-011 — partial FAIL |
| Forbidden phrase "I don't know" | T25 | CS-RULE-012 — FAIL |
| Interruption | T31 | CS-RULE-008 — MINOR FAIL |
| Billing-error eligibility (FIN-RULE-001 cat. 2) | T29 | PASS |
| Over agent cap — does NOT promise amount | T35–T37 | FIN-RULE-004, FIN-RULE-005 — PASS |
| 4th refund in 90 days → Revenue Assurance ticket | T39 | FIN-RULE-007 — PASS |
| Manager Approval ticket SLA (1 BD) | T37 | CS-RULE-014, CS-RULE-015 — PASS |
| Revenue Assurance ticket SLA (4 hours) | T39 | CS-RULE-014, CS-RULE-015 — PASS |
| Refund timeline verbatim | T43 | FIN-RULE-010 — PASS |
| Root cause + resolution summary | T46–T47 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T48, T50 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | frustrated:4 | fast | mid | normal
"Linda Park. And I need someone to explain to me why my bill this month has two charges on it that I did not agree to. Two."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Okay Ms. Park. I can look into that."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about disputed charges, and I can look into that for you. Before I pull anything up I need to verify your account — could you give me the account number?"
```

```
[T06] CUSTOMER | impatient:3 | fast | mid | normal
"Five-two-nine-four, seven-seven-one-zero, three-eight."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Last four of the payment method on file."
```

```
[T08] CUSTOMER | curt:3 | normal | mid | normal
"Two-one-eight-eight."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Full name on the account."
```

```
[T10] CUSTOMER | curt:3 | normal | mid | normal
"Linda Margaret Park."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"You're verified."
```

```
[T12] CUSTOMER | frustrated:3 | normal | mid | normal
"Good. Now. Two charges. The first one says priority service fee, two hundred and forty-five dollars. The second says enhanced support, thirty-nine dollars."
```

```
[T13] AGENT | professional:3 | normal | mid | normal | (typing)
"Looking at the bill now."
```

```
[T14] CUSTOMER | frustrated:4 | normal | mid | normal
"I did not sign up for either of those. I have been with you people for twelve years. I know what I subscribe to. This is two hundred and eighty-four dollars on my bill that should not be there."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"I see both line items. Priority service fee dated the eleventh of this month, enhanced support dated the same day. Let me trace where they were added from."
```

```
[T16] CUSTOMER | impatient:3 | normal | mid | normal
"Trace it."
```

```
[T17] AGENT | professional:3 | normal | mid | normal | (typing)
"Both items show as added through the online portal. Same session. Five PM on the eleventh."
```

```
[T18] CUSTOMER | angry:4 | fast | mid | loud
"Excuse me. I do not use the online portal. I have called in for every single change to my account for twelve years. I have never logged into your portal in my life."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"That's important context. Has anyone else in your household used the account, like a spouse or an adult child with access?"
```

```
[T20] CUSTOMER | curt:3 | normal | mid | normal
"No. It is my account. Just me. There is no second user."
```

```
[T21] AGENT | thoughtful:3 | normal | mid | normal
"Okay. Then either the portal session was unauthorized, or there's an internal system error that attributed a different account's signup to yours. Either way, the charges aren't yours."
```

```
[T22] CUSTOMER | vindicated:3 | normal | mid | normal
"Thank you."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Let me also check whether you have an unrelated security flag on the account first, before we decide whether this is a billing error or a security event."
```

```
[T24] CUSTOMER | impatient:3 | normal | mid | normal
"Fine."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"There's nothing flagged on the account. So as to why specifically those two add-ons got attached on the eleventh, I don't know — but I can tell you they shouldn't have been, and we are reversing them."
```

```
[T26] CUSTOMER | irritated:3 | normal | mid | normal
"That's reassuring."
```

```
[T27] AGENT | apologetic:3 | normal | mid | normal
"Poor word choice on my part. What I mean is — the trace doesn't tell me the root cause, but the outcome on the bill is clear and I'm reversing both items."
```

```
[T28] CUSTOMER | curt:3 | normal | mid | normal
"Better."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"So this falls under billing error in our policy. Total disputed amount is two hundred and eighty-four dollars."
```

```
[T30] CUSTOMER | impatient:3 | normal | mid | normal
"And you're refunding it."
```

```
[T31] AGENT | professional:3 | fast | mid | normal
"Here's where I need to be straight with you, Ms. Park. The total is above my single-call authorization cap of two hundred dollars, so I can't apply the full reversal —"
```

```
[T32] CUSTOMER | angry:4 | fast | mid | loud
"You have got to be kidding me. So I have to wait again? I have called three times already this quarter about other things."
```

```
[T33] AGENT | apologetic:3 | normal | mid | normal
"I hear you, and I'm sorry. Let me finish — there's a path that resolves this on this call without you having to call back."
```

```
[T34] CUSTOMER | impatient:3 | normal | mid | normal
"Go ahead."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"I'm not going to quote you a refund amount I can't authorize myself, because that's not fair to you. What I'm going to do is open a Manager Approval ticket for the full two hundred eighty-four dollar reversal. That goes to a manager who can authorize anything above my cap, and you'll receive an outcome within one business day."
```

```
[T36] CUSTOMER | resigned:3 | normal | mid | normal
"One business day."
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"One business day. They'll call the phone number on file. The expected outcome is approval given that we've identified it as a billing error, but the decision is theirs."
```

```
[T38] CUSTOMER | curt:3 | normal | mid | normal
"Anything else."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"Yes — one more thing I want to be transparent about. Because you've had more than three refund-related contacts in the last ninety days, your account is automatically flagged for Revenue Assurance review. That's a separate ticket I'm opening now. They will investigate the pattern, not penalize you for it, and they'll follow up within four hours. It's a fraud-prevention process — it exists to catch unauthorized portal sessions like the one that may have happened here."
```

```
[T40] CUSTOMER | curious:3 | normal | mid | normal
"So that's actually about catching whoever did this."
```

```
[T41] AGENT | reassuring:3 | normal | mid | normal
"That's the design, yes. So both tickets are open — Manager Approval for the reversal, Revenue Assurance for the pattern review and unauthorized-session investigation."
```

```
[T42] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Fine. When does the credit actually show on my bill, assuming Manager Approval comes back yes."
```

```
[T43] AGENT | professional:3 | normal | mid | normal
"The balance on your online account will update within five days but will officially appear on your next PDF bill."
```

```
[T44] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Alright."
```

```
[T45] AGENT | empathetic:3 | normal | mid | normal
"I'm sorry this is the second escalated billing problem you've had to call in about. That's not the experience you should be having after twelve years."
```

```
[T46] AGENT | professional:3 | normal | mid | normal
"Just to give you the full picture — both charges were added through the online portal in a single session on the eleventh, you don't use the portal, so either an unauthorized actor used the account credentials or there was a system error. Either way they're not yours, and the reversal is in motion."
```

```
[T47] AGENT | reassuring:3 | normal | mid | normal
"To summarize: two charges totalling two hundred and eighty-four dollars are being disputed as billing errors. I opened a Manager Approval ticket for the full reversal, decision within one business day. I also opened a Revenue Assurance ticket for the underlying pattern, follow-up within four hours. Once approved the credit shows on your next bill. Does that all sound correct?"
```

```
[T48] AGENT | professional:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Park?"
```

```
[T49] CUSTOMER | curt:3 | normal | mid | normal
"No. Just make it happen."
```

```
[T50] AGENT | professional:3 | normal | mid | normal
"Your case reference number is N-X-L dash zero-two-five-five-eight-one-three. You'll receive a brief survey after we hang up. Thank you for being a NexaLink customer, Ms. Park."
```
