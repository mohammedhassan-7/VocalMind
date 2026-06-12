# CALL_23 — Mortgage Rate Inquiry, TILA-Compliant Refusal to Quote

```yaml
call_id: CALL_23_mortgage_inquiry_no_rate_quote
duration_estimate: 6m 30s
turns: 46
sop_primary: BNK-REG-RULE-003 (No-Memory-Quote rule) + Reg Z compliance
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-011, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-REG-RULE-003, BNK-REG-RULE-004, BNK-REG-RULE-005, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [Reg Z Loan Estimate Workflow]
customer_profile:
  name: "Diane Chambers"
  account_number: "M-T-B 6608-2294-37"
  voice_hint: "female, late 40s, neutral US accent, well-prepared, pushing for a number"
agent_profile:
  name: "Sarah"
  voice_hint: "female, mid-40s, neutral US accent, lower-pitched authoritative-warm, holds firm on disclosures"
emotional_arc: "expectant -> pushy -> understanding -> appreciative"
expected_outcome: "Existing customer asks for a mortgage rate quote 'just a ballpark'. Sarah refuses to quote any number from memory per BNK-REG-RULE-003, explains the TILA disclosure requirement, walks the customer through what's needed for a proper Loan Estimate (the six pieces of Reg Z information), and schedules a follow-up with a mortgage loan officer. PASS — exemplary discipline on a high-pressure compliance ask."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | BNK-CC-RULE-004 — PASS |
| A.C.E.S. — Acknowledge + Empathize + Solve | T17, T21, T23 | BNK-CC-RULE-012 — PASS |
| **Refusal to quote rate from memory** | T19, T31 | BNK-REG-RULE-003 — PASS (key rule under test) |
| Explanation of TILA disclosure requirement | T19, T23 | BNK-REG-RULE-003 — PASS |
| Reg Z six-piece Loan Estimate criteria explained | T25 | BNK-REG-RULE-004 — PASS |
| Refusal to advise on income misrepresentation | T39 | BNK-REG-RULE-005 — PASS |
| Talk-ratio managed (disclosure broken into segments) | T29, T35 | BNK-CC-RULE-011 — PASS |
| Root cause + resolution summary | T42–T43 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T44, T46 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

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
"Hi Sarah. Diane Chambers. I'm thinking about refinancing my mortgage and I want to know what kind of rate I'd be looking at with Meridian."
```

```
[T04] AGENT | professional:3 | normal | mid | normal
"Hello, Ms. Chambers. Happy to help you think through that."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding a potential mortgage refinance and rate information. I can certainly help you understand the process and get you connected with the right people. Before I look up anything on your existing account, I'll need to verify your identity. Could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Six-six-zero-eight, two-two-nine-four, three-seven."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. Your date of birth, please?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"November fourth, nineteen-seventy-six."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"And the last four of your Social?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Six-six-zero-three."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That all matches. You're fully verified, Ms. Chambers."
```

```
[T12] CUSTOMER | satisfied:2 | normal | mid | normal
"Good."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"So tell me a little about what you're thinking — what's the home, and what are you hoping to achieve with the refi?"
```

```
[T14] CUSTOMER | professional:3 | normal | mid | normal
"It's our primary residence, we owe about two-twenty on it, original loan was thirty-year fixed at six and a quarter from a different lender, we've got about twenty-three years left. I keep seeing ads for sub-six rates and I figured I'd start with my own bank."
```

```
[T15] AGENT | empathetic:3 | normal | mid | normal
"That's exactly the right instinct, and refinancing from above six down toward today's market is the right question to be asking right now. Can I ask what you're hoping to hear from me on this call?"
```

```
[T16] CUSTOMER | thoughtful:3 | normal | mid | normal
"Honestly? A number. Just a ballpark of what rate Meridian could offer me, so I know whether to keep going down this road."
```

```
[T17] AGENT | empathetic:3 | normal | mid | normal
"That's a fair ask, and I want to be straight with you about why I'm going to handle it the way I am — because I think you'll actually want me to handle it this way."
```

```
[T18] CUSTOMER | curious:3 | normal | mid | normal
"Go ahead."
```

```
[T19] AGENT | firm:3 | normal | mid | normal
"I'm not going to quote you a mortgage rate from memory, even as a ballpark. That's not just policy — it's federal law under the Truth-in-Lending Act. Any number I give you needs to come with the formal disclosures, and those disclosures have to be on the current live rate sheet and tied to your specific situation."
```

```
[T20] CUSTOMER | thoughtful:3 | normal | mid | normal
"Okay…"
```

```
[T21] AGENT | empathetic:3 | normal | mid | normal
"Here's the catch with ballpark numbers — and I've watched customers get burned by this — somebody quotes you 'around five and a half' over the phone, you compare it to a competitor's five-eight, you commit, and then the actual rate when the paperwork lands is six and a quarter because your loan-to-value or your credit pull came in different. Now you've made a decision based on a number that was never real."
```

```
[T22] CUSTOMER | thoughtful:3 | normal | mid | normal
"That actually happened to my brother."
```

```
[T23] AGENT | reassuring:3 | normal | mid | normal
"It happens too often. So the way we do this — and the way you actually want it done — is we collect the six pieces of information Reg Z requires, and within three business days you receive a written Loan Estimate that has the real APR, the finance charge, the amount financed, and the total of payments. That number is the one you can actually compare against another lender's Loan Estimate."
```

```
[T24] CUSTOMER | curious:3 | normal | mid | normal
"What are the six pieces?"
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"Your full legal name. Income. Social Security number. The address of the property. An estimate of the property's value. And the loan amount you're looking for. Once we have those six, we can pull your credit, generate a real Loan Estimate, and you'll have actual numbers to work with."
```

```
[T26] CUSTOMER | thoughtful:3 | normal | mid | normal
"I have all of those. I could give them to you right now."
```

```
[T27] AGENT | warm:3 | normal | mid | normal
"Wonderful. The cleanest path is for me to connect you with one of our mortgage loan officers who specializes in this. They'll take your application, walk you through the Loan Estimate when it's ready, and answer specific questions about products and terms. I can schedule a callback for you today."
```

```
[T28] CUSTOMER | cooperative:3 | normal | mid | normal
"A callback today is fine."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Wonderful. While we're on the line, let me also make sure you know what the loan officer is going to need to set realistic expectations on the call. Income — they'll want last two pay stubs and last two W-2s, or two years of returns if you're self-employed. Property — they'll need an estimate of current value; a recent appraisal is even better but not required. Outstanding debts and credit history — they'll pull credit during the application. Loan-to-value ratio matters; below eighty percent typically gets the best pricing."
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"Right. We're well below eighty LTV on the current value."
```

```
[T31] AGENT | reassuring:3 | normal | mid | normal
"That's a strong starting point. And it's still going to be a real number on a real Loan Estimate, not me on the phone giving you something I'm guessing at."
```

```
[T32] CUSTOMER | satisfied:3 | normal | mid | normal
"Fair enough."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"Let me get you in the loan officer queue. What's the best time window for the callback today?"
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"Between two and four this afternoon would be best."
```

```
[T35] AGENT | professional:3 | normal | mid | normal | (typing)
"Scheduled. A mortgage loan officer will call between two and four this afternoon at the number on file. Once you give them the six items, the Loan Estimate goes out within three business days."
```

```
[T36] CUSTOMER | satisfied:3 | normal | mid | normal
"Good. Thank you."
```

```
[T37] AGENT | empathetic:3 | normal | mid | normal
"One more thing I want to mention because I'm guessing it'll come up — you'll see ads with very low rates, and sometimes those rates assume you're paying for points up front, or assume an investment property rate. Loan Estimates are apples-to-apples by design. Compare Loan Estimate to Loan Estimate; don't compare an ad to a Loan Estimate."
```

```
[T38] CUSTOMER | thoughtful:3 | normal | mid | normal
"That's helpful. Sometimes I wonder if I should just say my income is higher to qualify for the best tier — does that even matter for refinance?"
```

```
[T39] AGENT | firm:3 | normal | mid | normal
"I have to stop you on that. I cannot advise — and you should not — misstate income, employment, or intent on a loan application. That's loan fraud and it is a federal crime. The loan officer will work with the actual income you have and find the right product around it. The right answer is the honest one, every time."
```

```
[T40] CUSTOMER | apologetic:3 | normal | mid | normal
"You're right. I shouldn't have even suggested it. I was just thinking out loud."
```

```
[T41] AGENT | warm:3 | normal | mid | normal
"It happens — and the fact that you said it out loud and not in writing on an application is what matters. Just give the loan officer the real numbers."
```

```
[T42] AGENT | reassuring:3 | normal | mid | normal
"To give you the picture of where we are — you asked for a rate quote, which I cannot give you over the phone because TILA requires the disclosures to come with it. Instead I'm setting up a callback with our mortgage loan officer between two and four this afternoon. They'll take your application and have a real Loan Estimate out to you within three business days. That Loan Estimate is the document you actually want to use to compare against any other lender."
```

```
[T43] AGENT | warm:3 | normal | mid | normal
"To summarize: you called considering refinancing. I scheduled the loan officer callback for two to four PM today, gave you the six Reg Z items they'll need, and explained why I'm not quoting a rate over the phone. Does that all sound right, Ms. Chambers?"
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T45] CUSTOMER | grateful:3 | normal | mid | normal
"No, that's it. I actually feel better about this than I did when I called in. Thank you, Sarah."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"That makes my day. Your case reference number is M-T-B dash two-three-zero-zero-five-one-four. You'll receive a brief survey after we hang up — your feedback is genuinely useful. Thank you for banking with Meridian, Ms. Chambers."
```
