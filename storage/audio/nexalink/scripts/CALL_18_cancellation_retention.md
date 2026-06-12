# CALL_18 — Cancellation Intent, Retention Save

```yaml
call_id: CALL_18_cancellation_retention
duration_estimate: 7m 00s
turns: 50
sop_primary: SOP-05 (Customer Retention / Cancellation)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-011, CS-RULE-014, FIN-RULE-004, FIN-RULE-006, FIN-RULE-010, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 5.5 - Retention Playbook, Section 3.4 - Plan Catalog]
customer_profile:
  name: "Olivia Marchetti"
  account_number: "8810-5566-29"
  voice_hint: "female, mid-40s, neutral US accent, financially stretched and tired of comparing bills"
agent_profile:
  name: "Hannah"
  voice_hint: "female, mid-30s, low-mid composed register, calm and steady"
emotional_arc: "tired_firm -> heard -> open -> satisfied"
expected_outcome: "Customer calls intending to cancel due to price. Hannah validates the underlying concern (cost), asks open questions to understand usage patterns, and offers a downgrade-plus-loyalty-credit combination that meets the customer's monthly budget. Customer retains. Within agent cap. PASS — full SOP-05 retention save. Survey offered (CS-RULE-021 cancellation exception does NOT apply because the customer is staying)."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| A.C.E.S. — Acknowledge + Clarify + Empathize + Solve | T15–T25 | CS-RULE-011 — PASS |
| Retention playbook — discovery questions before offer | T17–T23 | SOP-05 — PASS |
| Downgrade + loyalty credit offer within cap | T23–T25 | FIN-RULE-004 — PASS |
| FIN-RULE-006 180-day courtesy check before applying | T35 | PASS (none in window) |
| Refund timeline verbatim | T40 | FIN-RULE-010 — PASS |
| Root cause + resolution summary | T44–T45 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T47, T50 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | tired:3 | normal | mid | normal
"Hi Hannah. This is Olivia Marchetti. Honestly, I'm calling to cancel my internet. The bill keeps creeping up and I just can't justify it anymore."
```

```
[T04] AGENT | empathetic:3 | normal | mid | normal
"Hi Ms. Marchetti, thank you for being upfront with me about that. I hear you, and bills creeping up is a real frustration. Let me see what we can do."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a cancellation due to cost, and I can certainly help you with that. Before I make any changes, I'll need to verify a few details — could you start with the account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Eight-eight-one-zero, five-five-six-six, two-nine."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thanks. And the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-four-one-seven."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"And the full name on the account?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Olivia Renee Marchetti."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified, Ms. Marchetti."
```

```
[T12] CUSTOMER | tired:2 | normal | mid | normal
"Okay, thanks."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"I can see you've been with us for almost four years, which is wonderful — and I can see your current plan is Home Pro Plus, the five hundred megabit plan, at seventy-nine dollars a month. Is that the bill that's creeping up?"
```

```
[T14] CUSTOMER | tired:3 | normal | mid | normal
"Yes. When I signed up it was sixty-something with the intro promo. Now it's seventy-nine plus the equipment fee plus tax. I'm paying close to ninety a month and my budget is tight."
```

```
[T15] AGENT | empathetic:4 | normal | mid | normal
"That's completely fair, and I'm sorry the intro pricing rolled off without something to soften the transition. Before I process anything either way, can I ask a few quick questions about how you actually use the internet? I don't want to push you to stay if it doesn't work for you, but I'd rather understand the picture before we decide."
```

```
[T16] CUSTOMER | tired:3 | normal | mid | normal
"Sure. Go ahead."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"Roughly how many people use the internet in your household on a typical day?"
```

```
[T18] CUSTOMER | thoughtful:3 | normal | mid | normal
"It's just me. My son moved out last year."
```

```
[T19] AGENT | thoughtful:3 | normal | mid | normal
"Got it. And what does a typical online day look like for you — mostly streaming and browsing, or work calls, or something heavier?"
```

```
[T20] CUSTOMER | thoughtful:3 | normal | mid | normal
"Mostly Netflix and some YouTube in the evenings. I work in person, so I don't do video calls from home. I might check email and shop online but that's it."
```

```
[T21] AGENT | warm:3 | normal | mid | normal
"That's really helpful. Here's what I'm seeing — the five hundred plan was a great fit when there were two of you and one was working from home. With one person, mostly Netflix, you are paying for a lot of headroom you aren't using."
```

```
[T22] CUSTOMER | curious:3 | normal | mid | normal
"Mm-hm."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"So before we cancel, I'd like to propose two changes together. First, drop the plan to Home Essentials — that's our hundred megabit tier, which is more than enough for streaming, browsing, and shopping. The list price on that is fifty-nine dollars."
```

```
[T24] CUSTOMER | thoughtful:3 | normal | mid | normal
"Okay…"
```

```
[T25] AGENT | reassuring:3 | normal | mid | normal
"Second — for loyalty, I can apply a fifteen-dollar-a-month credit for the next twelve months. That's a recurring credit, not a one-time, and it brings the plan effectively to forty-four dollars before the equipment fee."
```

```
[T26] CUSTOMER | surprised:3 | normal | mid | normal
"Forty-four? Really?"
```

```
[T27] AGENT | warm:3 | normal | mid | normal
"Forty-four for the service, plus the eight dollar equipment fee, plus tax. So you'd be looking at roughly fifty-five to fifty-eight dollars total each month for the next twelve months, instead of close to ninety."
```

```
[T28] CUSTOMER | thoughtful:3 | normal | mid | normal
"That's a real difference. I was paying about that when I first signed up."
```

```
[T29] AGENT | empathetic:3 | normal | mid | normal
"And honestly, this is closer to what your actual usage justifies. We were never going to deliver more value with the higher-tier plan if you weren't using it."
```

```
[T30] CUSTOMER | curious:3 | normal | mid | normal
"Is there a catch with the credit? Does it lock me in?"
```

```
[T31] AGENT | reassuring:3 | normal | mid | normal
"No contract extension required. Your current term doesn't change. The loyalty credit is month-to-month — if you ever decide to leave during the twelve months, no early-termination penalty is added by accepting this credit."
```

```
[T32] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay. That feels honest."
```

```
[T33] AGENT | warm:3 | normal | mid | normal
"Take a moment if you need to. No pressure — if forty-four plus equipment still doesn't fit the budget, we cancel today and there are no hard feelings."
```

```
[T34] CUSTOMER | thoughtful:3 | normal | mid | normal | (pause)
"No, that actually works. Let's do it. Downgrade and the credit."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"Wonderful. Before I apply the credit — I want to confirm I'm not stacking it against another courtesy credit in the same six-month window. Looking at your account… no courtesy credits in the last hundred and eighty days, so this applies cleanly within policy."
```

```
[T36] CUSTOMER | cooperative:3 | normal | mid | normal
"Good."
```

```
[T37] AGENT | professional:3 | normal | mid | normal | (typing)
"Applying the plan change from Home Pro Plus to Home Essentials, effective immediately. And applying the fifteen-dollar-a-month loyalty credit for twelve months, starting with the current cycle."
```

```
[T38] AGENT | reassuring:3 | normal | mid | normal
"Done. The plan change kicks in within fifteen minutes — you may want to power-cycle the router once. The loyalty credit will start showing on this cycle, pro-rated for the days left."
```

```
[T39] CUSTOMER | curious:3 | normal | mid | normal
"And the credit shows where exactly?"
```

```
[T40] AGENT | professional:3 | normal | mid | normal
"The balance on your online account will update within five days but will officially appear on your next PDF bill. You'll see two line items — Home Essentials at fifty-nine and a loyalty credit line showing negative fifteen — so it's transparent month by month."
```

```
[T41] CUSTOMER | satisfied:3 | normal | mid | normal
"Good. Thank you."
```

```
[T42] AGENT | warm:3 | normal | mid | normal
"You're very welcome. And I want to say — you came in ready to cancel, and you stayed because the numbers worked. That's the right reason."
```

```
[T43] CUSTOMER | grateful:3 | normal | mid | normal
"Yeah. I appreciate that you actually listened to what I was using it for."
```

```
[T44] AGENT | empathetic:3 | normal | mid | normal
"That's the part most people don't expect from a retention call — the questions about how you actually live with the service. But it's the only honest way to get to a real number."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you called considering cancellation due to cost, we downgraded your plan from Home Pro Plus to Home Essentials at fifty-nine dollars, applied a fifteen-dollar-a-month loyalty credit for the next twelve months, and your total monthly bill should drop to roughly fifty-five to fifty-eight dollars including equipment and tax. The plan change is live, the credit posts on your next bill. Does that all sound right?"
```

```
[T46] CUSTOMER | satisfied:3 | normal | mid | normal
"Yes. That's exactly what I wanted."
```

```
[T47] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Marchetti?"
```

```
[T48] CUSTOMER | grateful:3 | normal | mid | normal
"No, that's it. Thank you, Hannah."
```

```
[T49] AGENT | warm:3 | normal | mid | normal
"My pleasure."
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"Your case reference number is N-X-L dash one-eight-six-six-zero-three-four. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Thank you for staying with NexaLink, Ms. Marchetti. Have a great rest of your day."
```
