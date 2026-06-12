# CALL_27 — Small Business Loan Inquiry, TILA-Compliant Pre-Qualification

```yaml
call_id: CALL_27_business_loan_inquiry
duration_estimate: 7m 15s
turns: 50
sop_primary: BNK-SOP-01 (Account / Onboarding) + Reg Z disclosure path
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-007, BNK-CC-RULE-011, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-SEC-RULE-002, BNK-REG-RULE-002, BNK-REG-RULE-003, BNK-REG-RULE-004, BNK-REG-RULE-005, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [Business Banking Pre-Qualification Worksheet, Reg Z Loan Estimate Workflow]
customer_profile:
  name: "Marcus Whitaker"
  account_number: "M-T-B-BIZ 4419-6630-15"
  voice_hint: "male, late 40s, neutral US accent, owns a small commercial HVAC business, businesslike and prepared"
agent_profile:
  name: "Andre"
  voice_hint: "male, mid-30s, neutral US accent, friendly methodical cadence, business-banking specialist"
emotional_arc: "businesslike -> engaged -> appreciative -> satisfied"
expected_outcome: "Existing business customer asks about a $120K equipment loan to buy two new service vans. Andre completes business-account verification, collects the documentation requirements for the application, explains the Reg Z disclosure flow, schedules the credit pull and Loan Estimate. Does NOT quote a rate from memory (BNK-REG-RULE-003 PASS), does NOT advise on income misrepresentation (BNK-REG-RULE-005 PASS). Beneficial Ownership Rule verified per BNK-REG-RULE-002. PASS — full SOP."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification (business, control-person) | T07–T15 | BNK-CC-RULE-004 — PASS |
| Beneficial Ownership confirmation | T17 | BNK-REG-RULE-002 — PASS |
| Privacy data-use statement | T19 | BNK-SEC-RULE-002 — PASS |
| Refusal to quote rate from memory | T27, T35 | BNK-REG-RULE-003 — PASS |
| Reg Z six-piece collection scheduled | T31 | BNK-REG-RULE-004 — PASS |
| Reg Z 3-business-day Loan Estimate disclosed | T33 | BNK-REG-RULE-004 — PASS |
| Talk-ratio managed (broken into segments) | T29, T35 | BNK-CC-RULE-011 — PASS |
| A.C.E.S. light — Acknowledge + Empathize | T21, T39 | BNK-CC-RULE-012 — PASS |
| Refusal to advise income misrepresentation | T41 | BNK-REG-RULE-005 — PASS |
| Root cause + resolution summary | T44–T46 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T47, T50 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Andre, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | professional:3 | normal | mid | normal
"Andre, this is Marcus Whitaker, Whitaker Heating and Air. We're looking to add two new service vans to the fleet and I want to talk through financing options."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hi, Mr. Whitaker. Excellent — equipment financing is a big part of what I do. Glad you called."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding a small business equipment loan for two service vans, and I can certainly help you walk through that. Because we'll be looking at business-account information, I'll need to verify you as the control person on the account first."
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure."
```

```
[T07] AGENT | professional:3 | normal | mid | normal
"Could you give me the business account number?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-four-one-nine, six-six-three-zero, one-five."
```

```
[T09] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. The full legal business name as it appears on the account?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Whitaker Heating and Air Conditioning LLC."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"Your full legal name?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Marcus James Whitaker."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"And your date of birth?"
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"February eighteenth, nineteen-seventy-seven."
```

```
[T15] AGENT | reassuring:3 | normal | mid | normal
"All matches. I have you verified as the control person and sole member of Whitaker Heating and Air LLC."
```

```
[T16] CUSTOMER | satisfied:2 | normal | mid | normal
"Good."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"And our beneficial ownership records show you as the one hundred percent owner. Is that still accurate, or has anything changed in the past year?"
```

```
[T18] CUSTOMER | cooperative:3 | normal | mid | normal
"Still one hundred percent me. No changes."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"Wonderful. One brief standard statement — your information is used solely to provide and service your accounts, in accordance with our Privacy Notice and applicable law. You may receive a copy on request at any time."
```

```
[T20] CUSTOMER | neutral:2 | normal | mid | normal
"Understood."
```

```
[T21] AGENT | warm:3 | normal | mid | normal
"Tell me a little about the vans — what year, make, approximate cost, and what term you'd want on the financing?"
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Two twenty-twenty-six Ford Transits configured for HVAC service. About sixty thousand each delivered, so one-twenty total. I'd want to finance the full purchase, fifty-month or sixty-month term, whatever works best on the monthly."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Got it. So one hundred twenty thousand financed, looking at five-year amortization. Do you have a meaningful down payment in mind, or are you looking at the full amount?"
```

```
[T24] CUSTOMER | cooperative:3 | normal | mid | normal
"I can put fifteen thousand down if it helps the rate, but I'd rather keep cash for working capital if it doesn't make a meaningful difference."
```

```
[T25] AGENT | thoughtful:3 | normal | mid | normal
"That's a fair tradeoff to think about. A down payment does help the rate because it reduces our loan-to-value, but on equipment loans the rate movement from fifteen thousand down on a hundred-twenty loan is usually modest. Let me make sure the loan officer factors both scenarios into your Loan Estimate so you can compare side by side."
```

```
[T26] CUSTOMER | curious:3 | normal | mid | normal
"Speaking of rates — what kind of rate am I looking at?"
```

```
[T27] AGENT | firm:3 | normal | mid | normal
"That's the part I have to handle precisely. I'm not going to quote you a rate from memory — that's federal law under TILA. Any rate I give you has to come with the formal disclosures, which need to come from the live rate sheet at the time of your application. So instead of giving you a misleading ballpark, what I'm going to do is set up the formal application path."
```

```
[T28] CUSTOMER | cooperative:3 | normal | mid | normal
"Fair enough. Walk me through that."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"For a business equipment loan we'll need to collect a few things. Two years of business tax returns. Most recent year-end and current year-to-date profit and loss. Most recent two months of business bank statements — which I can pull internally since you're with us. A current balance sheet. The vendor invoice or purchase quote for the vans. And your personal financial statement, since you'll personally guarantee on a single-member LLC of this size."
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"I have all of that. I can have it to you by tomorrow morning."
```

```
[T31] AGENT | warm:3 | normal | mid | normal
"Wonderful. Once we have the package, the loan officer pulls credit, runs underwriting, and the Loan Estimate goes out — by regulation that has to be within three business days of receiving a complete application."
```

```
[T32] CUSTOMER | curious:3 | normal | mid | normal
"Three business days from when you have everything in hand?"
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"Exactly. Three business days from when the complete application is on file. The Loan Estimate will show you the APR, the finance charge, the amount financed, the total of payments. That's the document you'd compare against any other lender's quote."
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"And the rate I see on that — is that locked?"
```

```
[T35] AGENT | thoughtful:3 | normal | mid | normal
"The Loan Estimate locks the terms but not the rate, technically — the rate locks at the rate-lock step after you accept the estimate. The loan officer will walk you through both at the right step. The important thing is that everything is documented in writing."
```

```
[T36] CUSTOMER | satisfied:3 | normal | mid | normal
"Got it. Who's the loan officer?"
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"I'll route you to our commercial equipment specialist — a callback within two business hours of receiving your document package. Best phone window for you tomorrow morning?"
```

```
[T38] CUSTOMER | cooperative:3 | normal | mid | normal
"After ten AM. I have a morning service call before that."
```

```
[T39] AGENT | professional:3 | normal | mid | normal | (typing)
"Scheduling for after ten AM tomorrow. They'll review the package, run credit, and the Loan Estimate goes out within three business days from that point."
```

```
[T40] CUSTOMER | curious:3 | normal | mid | normal
"One more question — I'm self-employed, my income on tax returns looks lower than reality because of write-offs. Should I just give you a higher number on the application to make the ratios look better?"
```

```
[T41] AGENT | firm:3 | normal | mid | normal
"I have to stop you on that. No — I cannot advise that, and you should not do it. Misrepresenting income, employment, or intent on a loan application is loan fraud. It's a federal crime. The right approach for self-employed borrowers is what's called add-back analysis — the loan officer adds back legitimate non-cash expenses like depreciation and home office to the tax return income to get a true cash-flow number. That's the regulatory-acceptable way to present accurate income."
```

```
[T42] CUSTOMER | apologetic:3 | normal | mid | normal
"Good to know. I would not have thought to ask in any other way — appreciate you being direct on that."
```

```
[T43] AGENT | warm:3 | normal | mid | normal
"That's the right answer, every time. The loan officer will know exactly how to do the add-backs from your returns."
```

```
[T44] AGENT | reassuring:3 | normal | mid | normal
"So just to give you the picture — the call today is the intake call, not the application call. You'll submit your document package tomorrow, the loan officer will call you back the same day after ten AM, they'll review with you, pull credit, and within three business days you'll have a Loan Estimate in writing showing the actual rate, APR, fees, and monthly payment for your one-hundred-twenty-thousand-dollar equipment loan."
```

```
[T45] AGENT | professional:3 | normal | mid | normal
"If you want, we can also run two scenarios in parallel — full one-twenty financed versus fifteen thousand down — so you can see the rate and monthly side by side."
```

```
[T46] AGENT | reassuring:3 | normal | mid | normal
"To summarize: I verified you on the business account and as the control person, walked through the document package, scheduled a callback from our commercial equipment specialist after ten AM tomorrow, and explained the Reg Z Loan Estimate timeline. Two scenarios — full finance and fifteen down — will be on the Loan Estimate for side-by-side comparison. Does that all sound right, Mr. Whitaker?"
```

```
[T47] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T48] CUSTOMER | grateful:3 | normal | mid | normal
"No, that's a clear path. Appreciate you walking me through it properly, Andre. The self-employed income thing — I really did wonder if I was supposed to inflate to be competitive. Good to hear the actual answer."
```

```
[T49] AGENT | warm:3 | normal | mid | normal
"It's a question I hear all the time. You're not alone in asking it. The add-back analysis is exactly designed for your situation."
```

```
[T50] AGENT | professional:3 | normal | mid | normal
"Your case reference number is M-T-B dash two-seven-zero-zero-six-six-five. You'll receive a brief survey after we hang up — appreciate the feedback if you have a moment. Thanks for banking with Meridian, Mr. Whitaker."
```
