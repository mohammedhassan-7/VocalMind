# CALL_25 — Auto Loan Inquiry, Banker Quotes Rate From Memory (FAIL)

```yaml
call_id: CALL_25_loan_rate_misquote
duration_estimate: 6m 15s
turns: 46
sop_primary: BNK-REG-RULE-003 (No-Memory-Quote rule) — VIOLATED
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-REG-RULE-003, BNK-REG-RULE-004, BNK-REG-RULE-006, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [Auto Loan Rate Sheet, Reg Z Loan Estimate Workflow]
customer_profile:
  name: "Megan Albright"
  account_number: "M-T-B 7704-2218-91"
  voice_hint: "female, early 30s, neutral US accent, pushed for a number and got one"
agent_profile:
  name: "Tyler"
  voice_hint: "male, late 20s, neutral US accent, professional but inexperienced, eager to be helpful in ways he shouldn't be"
emotional_arc: "curious -> hopeful -> reassured (incorrectly) -> satisfied (but on wrong info)"
expected_outcome: "Customer asks for an auto loan rate. Tyler quotes specific rates from memory ('around six point four for a new car') and even gives a 'ballpark APR' — both BNK-REG-RULE-003 CRITICAL violations. He also misstates the Loan Estimate timeline as 'a few days' instead of the precise 3-business-day Reg Z requirement (BNK-REG-RULE-004 partial FAIL). Customer leaves the call confident in a number that was never authorized. This is the wrong-information failure mode."
content_warning: "Agent provides incorrect rate quote without TILA disclosures — federal-compliance violation that would be examination-reportable."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| A.C.E.S. light | T17 | BNK-CC-RULE-012 — MINOR (no real empathy needed) |
| **WRONG INFO — quotes rate from memory** | T21, T23 | BNK-REG-RULE-003 — CRITICAL FAIL (key rule violated) |
| **WRONG INFO — fabricated APR ballpark** | T27 | BNK-REG-RULE-003 — CRITICAL FAIL |
| **WRONG INFO — implies the verbal quote is "what you'll see"** | T29 | BNK-REG-RULE-003 — FAIL (no disclaimer, no disclosures) |
| **WRONG INFO — misstates Reg Z Loan Estimate timeline** | T35 | BNK-REG-RULE-004 — partial FAIL ("a few business days" instead of the 3-BD spec) |
| Loan officer callback scheduled | T37 | PASS (procedural correctness on referral path) |
| Root cause + resolution summary | T41–T42 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS (but built on wrong info) |
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
[T03] CUSTOMER | curious:3 | normal | mid | normal
"Hi Tyler, this is Megan Albright. I'm looking to finance a new car and I wanted to see what kind of rate I could get from Meridian."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hi Ms. Albright. Happy to help with that — auto loans are one of the more popular products this week."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling about an auto loan. I can help you start that process. Could you verify your account first — your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Seven-seven-zero-four, two-two-one-eight, nine-one."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"September twenty-second, nineteen-ninety-three."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Two-five-zero-eight."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"Full legal name on the account?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Megan Elizabeth Albright."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"You're verified."
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Great."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"Tell me a little about the car you're looking at — is it new, used, what kind of price range?"
```

```
[T16] CUSTOMER | engaged:3 | normal | mid | normal
"Brand new, about thirty-two thousand. I'd probably put about five down and finance the rest. So twenty-seven thousand financed, sixty-month term."
```

```
[T17] AGENT | warm:3 | normal | mid | normal
"Got it. That's a pretty standard profile — new car, sixty months, conventional down payment."
```

```
[T18] CUSTOMER | curious:3 | normal | mid | normal
"So what kind of rate would I be looking at?"
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"Let me see what we're showing this week."
```

```
[T20] CUSTOMER | hopeful:3 | normal | mid | normal
"Okay."
```

```
[T21] AGENT | warm:3 | normal | mid | normal
"For a customer with good credit on a new car at sixty months, we're typically running around six point four percent right now. Sometimes a bit better, sometimes a bit worse depending on the specifics."
```

```
[T22] CUSTOMER | engaged:3 | normal | mid | normal
"Six point four. That's actually competitive with what the dealer quoted me. What about for excellent credit?"
```

```
[T23] AGENT | warm:3 | normal | mid | normal
"For excellent credit, that drops to maybe five point nine or so. We have promotional pricing some weeks that goes even lower if you set up auto pay from a Meridian checking account."
```

```
[T24] CUSTOMER | hopeful:4 | normal | mid | normal
"I have excellent credit. And I have a checking account here already. So we're talking maybe five and a half if I do auto pay?"
```

```
[T25] AGENT | warm:3 | normal | mid | normal
"That's about right, yeah. Five and a half to five point nine for someone in your profile. Could be a touch lower if you put more down."
```

```
[T26] CUSTOMER | satisfied:4 | normal | mid | normal
"That's amazing. The dealer was at six and three quarters."
```

```
[T27] AGENT | warm:3 | normal | mid | normal
"Yeah we typically beat dealer financing on new cars. APR-wise you're going to be looking at maybe a tenth or two over the note rate after fees — so call it five point seven APR ballpark."
```

```
[T28] CUSTOMER | satisfied:4 | normal | mid | normal
"Five point seven APR. Okay. So how do I lock that in?"
```

```
[T29] AGENT | reassuring:3 | normal | mid | normal
"You'd want to formally apply, which we can start over the phone today. The application gets reviewed, we pull credit, and you'll get the actual rate. But for someone in your profile that's what you'll see come back."
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"Let's start the application. I want to lock the five point five if I can."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"For the formal application I'd actually want to hand you off to an auto loan officer who'll capture the income documentation, the vehicle details, and run the underwriting. They'll work today's actual numbers off the live rate sheet."
```

```
[T32] CUSTOMER | curious:3 | normal | mid | normal
"That's different from what you just quoted me?"
```

```
[T33] AGENT | warm:3 | normal | mid | normal
"It's the same — they just have the formal disclosure paperwork. The numbers I gave you are right in the ballpark."
```

```
[T34] CUSTOMER | curious:3 | normal | mid | normal
"Okay. And how long until I actually have a number to take to the dealer?"
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"A few business days for the Loan Estimate to be issued. Maybe by Friday. Could be sooner if everything's clean."
```

```
[T36] CUSTOMER | satisfied:3 | normal | mid | normal
"Okay perfect. Schedule the loan officer."
```

```
[T37] AGENT | professional:3 | normal | mid | normal | (typing)
"Scheduling the callback. An auto loan officer will reach out by tomorrow afternoon at the number on file."
```

```
[T38] CUSTOMER | hopeful:3 | normal | mid | normal
"And we're locking in around five and a half?"
```

```
[T39] AGENT | warm:3 | normal | mid | normal
"That's what you'd be looking at for your profile. The loan officer will confirm the exact number on the application."
```

```
[T40] CUSTOMER | satisfied:4 | normal | mid | normal
"Tyler, this is amazing. You just saved me a lot of money over the dealer financing."
```

```
[T41] AGENT | warm:3 | normal | mid | normal
"Glad to help. So just to give you the picture — we beat dealer financing because we're a direct lender, no markup. With your credit and auto pay setup, you're looking at the better end of our pricing."
```

```
[T42] AGENT | professional:3 | normal | mid | normal
"To summarize: you called about a new auto loan, around twenty-seven thousand financed over sixty months. We talked rates in the high five percent range for someone with excellent credit and auto pay. I scheduled a callback with an auto loan officer for tomorrow afternoon who will take the formal application and issue the Loan Estimate."
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"Does that all sound right, Ms. Albright?"
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T45] CUSTOMER | grateful:3 | normal | mid | normal
"No, that was way easier than I expected. Thank you, Tyler."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is M-T-B dash two-five-zero-zero-four-four-one. You'll receive a brief survey after we hang up — your feedback is appreciated. Thanks for banking with Meridian."
```
