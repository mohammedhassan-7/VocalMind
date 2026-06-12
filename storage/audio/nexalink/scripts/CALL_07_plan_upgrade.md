# CALL_07 — Plan Upgrade (Home Internet 100 → 500 Mbps)

```yaml
call_id: CALL_07_plan_upgrade
duration_estimate: 5m 15s
turns: 38
sop_primary: SOP-02 (Billing Issue Resolution / Plan Changes)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, SEC-RULE-002, SEC-RULE-003, CS-RULE-007, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.4 - Plan Catalog, Section 3.7 - Proration Rules]
customer_profile:
  name: "James Albright"
  account_number: "7204-1865-22"
  voice_hint: "male, 40s, neutral US accent, businesslike but friendly"
agent_profile:
  name: "Priya"
  voice_hint: "female, 30s, neutral US accent, warm and measured"
emotional_arc: "curious -> engaged -> decisive -> satisfied"
expected_outcome: "Plan upgraded from 100 Mbps to 500 Mbps effective immediately. Pro-rated charge for current cycle disclosed. No ticket required. Survey offered."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T05–T11 | account number + last 4 of payment + full name — PASS |
| Privacy data-use statement | T13 | SEC-RULE-002 — PASS |
| PCI compliance (only last 4 referenced) | T07 | SEC-RULE-003 — PASS |
| Context explanation | T17–T21 | CS-RULE-018 — PASS |
| Resolution summary | T34 | CS-RULE-019 — PASS |
| Anything else + case ref + survey | T36, T38 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | curious:3 | normal | mid | normal
"Hi Priya, this is James Albright. I'm thinking about upgrading my internet plan and wanted to talk through the options."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hello, Mr. Albright. Happy to help with that."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling regarding a plan upgrade, and I can certainly help you with that. Before I can pull up your account, I'll need to verify a few details. Could you start with your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure. Seven-two-zero-four, one-eight-six-five, two-two."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And could you confirm the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"Last four are oh-nine-five-seven."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And finally — could you confirm the full name on the account?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"James Robert Albright."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified, Mr. Albright."
```

```
[T12] CUSTOMER | neutral:2 | normal | mid | normal
"Great."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Your data is used solely for service provisioning and support quality, in accordance with our Privacy Policy."
```

```
[T14] CUSTOMER | neutral:2 | normal | mid | normal
"Understood."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"So I can see you're currently on our hundred-megabit Home Essentials plan at fifty-nine dollars a month. What's driving the interest in upgrading?"
```

```
[T16] CUSTOMER | thoughtful:3 | normal | mid | normal
"We've got two teenagers and both my wife and I work from home now. The hundred is just not cutting it on video calls."
```

```
[T17] AGENT | empathetic:3 | normal | mid | normal
"That makes a lot of sense — four heavy users on a hundred-megabit line is genuinely tight, especially with video. Let me walk you through what's available."
```

```
[T18] CUSTOMER | curious:3 | normal | mid | normal
"Sure, go ahead."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"The next tier up is our Home Pro plan at three hundred megabits, sixty-nine dollars a month. Above that is Home Pro Plus at five hundred megabits, seventy-nine a month. And our top consumer tier is Gigabit Home at a thousand megabits, ninety-nine a month. All three include the same equipment and the same unlimited data."
```

```
[T20] CUSTOMER | thoughtful:3 | normal | mid | normal
"Hmm. What would you recommend for two work-from-home adults plus two teenagers gaming and streaming?"
```

```
[T21] AGENT | thoughtful:3 | normal | mid | normal
"Honestly, the five-hundred plan tends to be the sweet spot for households like yours. It handles simultaneous four-K streams and video calls comfortably without paying for headroom you wouldn't use. Gigabit is real, but most households don't saturate it."
```

```
[T22] CUSTOMER | satisfied:3 | normal | mid | normal
"Okay, let's go with the five hundred."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Excellent choice. So I'll be moving you from Home Essentials at fifty-nine dollars to Home Pro Plus at seventy-nine dollars, an increase of twenty dollars on your monthly bill."
```

```
[T24] CUSTOMER | neutral:3 | normal | mid | normal
"Right."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"Since we're partway through your current billing cycle, this cycle will show a small pro-rated charge for the upgraded plan from today through your bill date. That comes out to about thirteen dollars and thirty cents. Your next full bill will then show the new plan at seventy-nine dollars."
```

```
[T26] CUSTOMER | curious:3 | normal | mid | normal
"And the upgraded speed — when does that kick in?"
```

```
[T27] AGENT | reassuring:3 | normal | mid | normal
"As soon as I apply the change, the new speed is provisioned on your modem within about fifteen minutes. You may need to power-cycle the router once for it to pick up the higher cap."
```

```
[T28] CUSTOMER | satisfied:3 | normal | mid | normal
"Okay. Yeah, let's do it."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Confirming: upgrade to Home Pro Plus, five hundred megabits, seventy-nine dollars monthly, effective immediately, with a thirteen-dollar-thirty cent pro-rated charge on the current cycle. Is that correct?"
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes, that's right."
```

```
[T31] AGENT | professional:3 | normal | mid | normal | (typing)
"Applying it now."
```

```
[T32] AGENT | warm:3 | normal | mid | normal
"And it's done. The new plan is live on your account."
```

```
[T33] CUSTOMER | satisfied:3 | normal | mid | normal
"Wow, that was fast."
```

```
[T34] AGENT | reassuring:3 | normal | mid | normal
"To summarize: I upgraded your Home Essentials plan to Home Pro Plus at five hundred megabits per second. A pro-rated charge of thirteen dollars and thirty cents will appear on this cycle's bill, and from next cycle onward you'll see the seventy-nine dollar monthly rate. The new speed should be active within fifteen minutes once you power-cycle the router. Does that all sound right?"
```

```
[T35] CUSTOMER | grateful:3 | normal | mid | normal
"Sounds perfect. Thank you."
```

```
[T36] AGENT | warm:3 | normal | mid | normal
"My pleasure. Is there anything else I can help you with today, Mr. Albright?"
```

```
[T37] CUSTOMER | calm:2 | normal | mid | normal
"No, that's it. Appreciate the help."
```

```
[T38] AGENT | warm:3 | normal | mid | normal
"Your case reference number is N-X-L dash seven-seven-two-zero-five-five-eight. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Thank you for being a NexaLink customer, Mr. Albright. Have a great rest of your day."
```
