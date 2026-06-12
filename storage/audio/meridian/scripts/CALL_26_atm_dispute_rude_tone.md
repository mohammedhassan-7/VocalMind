# CALL_26 — Reg E ATM Dispute, Dismissive Agent Tone

```yaml
call_id: CALL_26_atm_dispute_rude_tone
duration_estimate: 6m 45s
turns: 48
sop_primary: BNK-SOP-02 (Reg E Dispute Resolution)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-008, BNK-CC-RULE-009, BNK-CC-RULE-011, BNK-CC-RULE-012, BNK-CC-RULE-014, BNK-SEC-RULE-001, BNK-REG-RULE-007, BNK-REG-RULE-008, BNK-FIN-RULE-004, BNK-FIN-RULE-005, BNK-FRAUD-RULE-002, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-02 Reg E Dispute Resolution]
customer_profile:
  name: "Tamika Pearson"
  account_number: "M-T-B 5510-3327-08"
  voice_hint: "female, mid-30s, neutral US accent, frustrated by both the disputed charges AND the agent's tone"
agent_profile:
  name: "Tyler"
  voice_hint: "male, late 20s, neutral US accent, professional but curt and impatient on this call"
emotional_arc: "frustrated -> hurt -> angry -> partially_satisfied"
expected_outcome: "Customer reports $120 in unauthorized ATM withdrawals from a card she has in her possession. Tyler is CURT throughout, talks over the customer twice (BNK-CC-RULE-009 FAIL), exceeds the 45% talk ratio (BNK-CC-RULE-011 informal FAIL), and MATCHES the customer's rising tension instead of de-escalating (BNK-CC-RULE-014 FAIL). He does eventually take the Reg E claim correctly and issues the provisional credit within his $500 cap (BNK-FIN-RULE-004 PASS). Outcome: dismissive tone, half-correct procedure on Reg E."
content_warning: "Agent is rude and dismissive; customer becomes visibly hurt."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — minimal, no empathy — MINOR |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| Talks over customer | T15, T17 | BNK-CC-RULE-009 — FAIL |
| Skips Empathize in A.C.E.S. | T21 | BNK-CC-RULE-012 — FAIL |
| Tone match — agent volume rises | T25 | BNK-CC-RULE-014 — FAIL |
| Talks over customer #2 | T29 | BNK-CC-RULE-009 — FAIL (2nd offense) |
| Talk-ratio / impatience cluster | T17, T29 | BNK-CC-RULE-011 — MINOR FAIL |
| Card closed + replacement ordered | T32–T33 | BNK-FRAUD-RULE-002 — PASS |
| Reg E claim accepted verbally without written form | T35 | BNK-REG-RULE-008 — PASS |
| Provisional credit within $500 cap | T37 | BNK-FIN-RULE-004 — PASS |
| Reg E timeline verbatim (10-day determination) | T39 | BNK-REG-RULE-007, BNK-FIN-RULE-005 — PASS |
| Root cause + resolution summary | T44–T45 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T46, T48 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

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
[T03] CUSTOMER | frustrated:3 | normal | mid | normal
"Hi Tyler. My name is Tamika Pearson. I have two ATM withdrawals on my account I did not make. Sixty dollars each. I need them disputed."
```

```
[T04] AGENT | curt:3 | normal | mid | normal
"Okay. Let me get you verified."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a dispute. I'll need to verify the account first — could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Five-five-one-zero, three-three-two-seven, zero-eight."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth."
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"June fifteenth, nineteen-eighty-eight."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social."
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Eight-eight-three-one."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"Full name on the account."
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Tamika Renee Pearson."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Verified. What's the dispute?"
```

```
[T14] CUSTOMER | concerned:3 | normal | mid | normal
"There are two ATM withdrawals from yesterday on my account. Sixty dollars each at an ATM in Phoenix Arizona. I am in Atlanta. I have my card in my hand right now. I —"
```

```
[T15] AGENT | curt:3 | fast | mid | normal
"Have you reported the card lost? Or do you still have it?"
```

```
[T16] CUSTOMER | confused:3 | normal | mid | normal
"I literally just said I have it in my hand. That's what I was telling you."
```

```
[T17] AGENT | curt:3 | fast | mid | normal
"Right. So it's a skimming situation — somebody cloned your card. Happens all the time. I'm going to close the card and issue a new one. What's the address on file —"
```

```
[T18] CUSTOMER | frustrated:3 | normal | mid | normal
"You just talked over me again."
```

```
[T19] AGENT | apologetic:3 | normal | mid | normal
"Sorry. Go ahead."
```

```
[T20] CUSTOMER | concerned:3 | normal | mid | normal
"I was going to say — the second one cleared my account into overdraft. So I'm now also being charged an overdraft fee on top of the unauthorized withdrawals."
```

```
[T21] AGENT | curt:3 | normal | mid | normal
"Okay. The overdraft fee will be reversed as a downstream of the dispute. I need to keep moving so we can get the provisional credit issued today."
```

```
[T22] CUSTOMER | distressed:3 | normal | mid | normal
"Are you in a hurry to get off this call or something?"
```

```
[T23] AGENT | curt:3 | normal | mid | normal
"I'm trying to be efficient. Do you want me to keep processing or do you want to talk about my tone?"
```

```
[T24] CUSTOMER | frustrated:4 | normal | mid | loud
"I want both, Tyler. I want you to take this seriously and stop rushing me."
```

```
[T25] AGENT | curt:3 | normal | mid | loud
"I am taking it seriously. Two ATM withdrawals, skimmed card, sixty plus sixty, plus the overdraft fee. I'm going to issue provisional credit for the disputed transactions, reverse the fee, and close the card. That's the procedure."
```

```
[T26] CUSTOMER | distressed:4 | normal | mid | normal
"Wow. Okay."
```

```
[T27] AGENT | apologetic:3 | normal | mid | normal
"That came out wrong. I'm sorry. Let me start over a bit."
```

```
[T28] CUSTOMER | curt:3 | normal | mid | normal
"Please."
```

```
[T29] AGENT | professional:3 | fast | mid | normal
"What I should have said is — yes, your card was likely skimmed, that's not your fault, and you have full Regulation E protections. I'm going to walk you through what I'm doing —"
```

```
[T30] CUSTOMER | frustrated:3 | normal | mid | normal
"Then walk me through it. Without rushing this time."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"Sure. I'm going to do this in four steps."
```

```
[T32] AGENT | professional:3 | normal | mid | normal
"Step one — closing your card right now so nobody else can use the cloned version. Card is closed."
```

```
[T33] AGENT | professional:3 | normal | mid | normal | (typing)
"Step two — ordering a replacement card. Standard delivery is three to five business days. Because this is fraud, the expedited shipping fee is waived. You can also have it expedited if you want it tomorrow — same waiver."
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"Tomorrow would be best. Yes."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"Step three — opening the Reg E dispute. I'm taking this as a verbal claim, which is your right under Regulation E. You don't need to sign a paper before I issue provisional credit, but the written claim will follow within ten business days — we'll mail it to you and you just sign and return it."
```

```
[T36] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay."
```

```
[T37] AGENT | professional:3 | normal | mid | normal | (typing)
"Step four — issuing provisional credit. Total disputed is one hundred and twenty dollars, plus the overdraft fee of seventy-seven dollars that was a downstream of the disputed transaction. Total provisional credit one hundred ninety-seven dollars. That's well within my five hundred dollar authority cap, so I can issue it now."
```

```
[T38] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"I am issuing a provisional credit of one hundred ninety-seven dollars today while we investigate. You will receive a written determination within ten business days. If the investigation requires additional time the timeline may extend, but the provisional credit remains in place during that period."
```

```
[T40] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay."
```

```
[T41] AGENT | professional:3 | normal | mid | normal
"Provisional credit posted to the account. You should see it as available balance immediately."
```

```
[T42] CUSTOMER | curious:3 | normal | mid | normal
"And if the investigation comes back in my favour, the credit stays?"
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"That's right. The final written determination will confirm. If by some unusual chance the investigation came back the other way, the credit would be reversed and you'd get a written explanation. But for an obvious skimming case at an ATM in a city you weren't in, with your card in your possession, the outcome should be straightforward."
```

```
[T44] AGENT | professional:3 | normal | mid | normal
"Just to give you the picture — your card was likely cloned at an ATM or merchant terminal somewhere you previously used it. Skimming devices read the magnetic stripe and PIN. The criminal then made a duplicate card and used it in Phoenix. Closing the card stops further losses. The replacement card will have a new number and PIN."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported two unauthorized ATM withdrawals totaling one hundred twenty dollars plus an overdraft fee of seventy-seven dollars. I closed the compromised card, ordered an expedited replacement for tomorrow delivery, opened a Reg E dispute, and issued provisional credit of one hundred ninety-seven dollars today. Written determination within ten business days. Does that all sound right?"
```

```
[T46] AGENT | professional:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Pearson?"
```

```
[T47] CUSTOMER | curt:3 | normal | mid | normal
"No. And next time please slow down. People are calling because they're already upset. Don't make it worse."
```

```
[T48] AGENT | apologetic:3 | normal | mid | normal
"That's fair. I'll take that. Your case reference number is M-T-B dash two-six-one-zero-zero-seven-nine. You'll receive a brief survey after we hang up. Thank you for being a Meridian customer."
```
