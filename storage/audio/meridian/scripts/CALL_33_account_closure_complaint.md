# CALL_33 — Account Closure Complaint, Partial Retention Save

```yaml
call_id: CALL_33_account_closure_complaint
duration_estimate: 7m 00s
turns: 50
sop_primary: BNK-SOP-04 (Account Closure & Retention)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-012, BNK-CC-RULE-014, BNK-SEC-RULE-001, BNK-FIN-RULE-001, BNK-FIN-RULE-002, BNK-FIN-RULE-003, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-04 Account Closure & Retention]
customer_profile:
  name: "Patricia Salinger"
  account_number: "M-T-B 2207-8843-19"
  voice_hint: "female, mid-50s, neutral US accent, calmly furious about cascading fees, has already moved most of her money elsewhere"
agent_profile:
  name: "Karen"
  voice_hint: "female, mid-30s, composed low-mid register, holds steady under pressure, retention specialist"
emotional_arc: "frustrated -> heard -> open -> partially_satisfied"
expected_outcome: "Long-tenure customer (eleven years) wants to close her checking and savings accounts after a string of fees she views as predatory. Karen runs A.C.E.S., does proper discovery (BNK-SOP-04 Step 1), and offers a policy-compliant retention package: waive the most recent $77 overdraft fee + switch to a no-fee checking product. Customer accepts the fee waiver but PROCEEDS with closing the savings account (she's already moved that money). Partial retention. Karen processes the closure cleanly, including auto-pay warnings and dormant-balance handling. NO survey offered per BNK-CC-RULE-023 exception. PASS — full SOP-04, honest one-offer-then-respect-the-decision."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| A.C.E.S. — Acknowledge + Clarify + Empathize + Solve | T15–T25 | BNK-CC-RULE-012 — PASS |
| Retention discovery before any offer | T17, T21 | BNK-SOP-04 Step 1 — PASS |
| Tone adapted (lower, calmer) | T15, T19 | BNK-CC-RULE-014 — PASS |
| One retention offer, no pressure beyond | T23–T29 | BNK-SOP-04 Step 2 — PASS |
| Fee waiver within $250 cap | T31, T34 | BNK-FIN-RULE-001 — PASS |
| BNK-FIN-RULE-003 180-day check before applying | T23 | PASS (none in window) |
| Partial closure (savings) processed cleanly | T35–T41 | BNK-SOP-04 Step 3 — PASS |
| Auto-pay warning before closure | T38 | BNK-SOP-04 — PASS |
| Balance disposition confirmed | T37, T41 | BNK-SOP-04 — PASS |
| Final-statement timeline disclosed | T41 | BNK-SOP-04 — PASS |
| Root cause + resolution summary | T44–T45 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| **NO survey on confirmed-cancellation portion** | T50 | BNK-CC-RULE-023 exception — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Karen, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | frustrated:4 | normal | mid | normal
"This is Patricia Salinger. I am calling to close my checking and savings accounts with Meridian. I have been a customer for over eleven years, but I am done with the fees."
```

```
[T04] AGENT | empathetic:3 | normal | mid | normal
"Hello, Ms. Salinger. Thank you for telling me straight up what brought you in today. I'll absolutely help you process the closure. I'd also like to understand what happened, both because policy asks me to, and frankly because eleven years is a long relationship to end without me at least listening."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding closing your checking and savings accounts. I can certainly help with that. Before I make any changes, I'll need to verify a few details. Could you start with the checking account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Two-two-zero-seven, eight-eight-four-three, one-nine."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"April fifteenth, nineteen-seventy."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Eight-eight-two-six."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the full legal name on the account?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Patricia Anne Salinger."
```

```
[T13] AGENT | reassuring:3 | normal | mid | normal
"That all matches. You're fully verified, Ms. Salinger."
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Good."
```

```
[T15] AGENT | empathetic:3 | slow | low | normal
"You mentioned fees. Would you mind sharing what specifically pushed you to call today? I'm not asking to argue back — I just need to understand."
```

```
[T16] CUSTOMER | frustrated:4 | normal | mid | normal
"It's been building. Last month it was a thirty-five dollar foreign transaction fee on a charge I didn't even know was foreign. Three months ago, a maintenance fee on the savings account because the balance dropped below some minimum nobody warned me about. And then last week — a seventy-seven dollar overdraft fee on the checking account that triggered because of a delay between my paycheck deposit and an auto-pay. I have already moved my main savings to a credit union. The only reason I haven't closed both already is I wanted to do it properly."
```

```
[T17] AGENT | empathetic:4 | normal | low | normal
"That's a fair list, Ms. Salinger. And eleven years of relationship plus three real fee complaints, and one of them an unwarned dormant-balance fee — that's the kind of pattern that should be addressable. Let me ask one clarifying thing — when you say you've moved your main savings, has the savings account here actually been down to near zero, or is there still meaningful balance there?"
```

```
[T18] CUSTOMER | cooperative:3 | normal | mid | normal
"There's about fifteen hundred left in savings just because I forgot to move the last bit. Checking has about three thousand."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"Got it. So practically speaking — savings is already dormant in your mind, checking is still actively used for your paycheck and auto-pay."
```

```
[T20] CUSTOMER | cooperative:3 | normal | mid | normal
"Correct."
```

```
[T21] AGENT | thoughtful:3 | normal | mid | normal
"So here's what I'd like to propose, and you can take any part or none of it — your decision either way and I will absolutely process whatever you choose."
```

```
[T22] CUSTOMER | curious:3 | normal | mid | normal
"Go ahead."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"First — the seventy-seven dollar overdraft fee last week, the one triggered by the paycheck-timing issue. I can waive that today within my authority since it's your first courtesy waiver in over six months. So that fee gets refunded."
```

```
[T24] CUSTOMER | satisfied:3 | normal | mid | normal
"Good. That one was the most aggravating."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"Second — I'd like to switch your checking account from the current Premium Checking to our Essentials Checking product. Essentials has no monthly maintenance fee regardless of balance, no minimum balance requirement, and free overdraft transfer if you link the savings or another account. That removes the structural piece that caused two of your three complaints."
```

```
[T26] CUSTOMER | thoughtful:3 | normal | mid | normal
"That actually would have helped."
```

```
[T27] AGENT | empathetic:3 | normal | mid | normal
"Honestly, it should have been suggested to you a long time ago. The Essentials product wasn't around eleven years ago, but it's been around for the last four, and it would have been a better fit for how you actually use the checking account."
```

```
[T28] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Right."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"And third — the savings account, with fifteen hundred left. If you want to keep it open, I can move it to a savings product with no balance-based maintenance fee, so the fifteen hundred isn't subject to the dormant fee that triggered the other complaint. Or — and this is completely your call — if you really are done with savings here and want to close it cleanly today, I'll do that and we'll send you the fifteen hundred wherever you want it."
```

```
[T30] CUSTOMER | thoughtful:3 | normal | mid | normal | (pause)
"Honestly… I think the truthful answer is that I want to keep checking here because of the paycheck setup, but I really do want savings closed. I'm not going to use it again. I'm trying to consolidate at the credit union for savings."
```

```
[T31] AGENT | warm:3 | normal | mid | normal
"That's an honest answer and a clean one. So here's what we'll do — partial retention. I keep checking with you, switch it to Essentials, waive the seventy-seven dollar fee from last week, and close the savings account cleanly today."
```

```
[T32] CUSTOMER | satisfied:3 | normal | mid | normal
"Yes. That's the right answer."
```

```
[T33] AGENT | professional:3 | normal | mid | normal | (typing)
"Step one — switching checking from Premium Checking to Essentials Checking. Done. No monthly fee, no minimum balance going forward. The transition keeps your account number and direct deposit setup intact, so nothing changes on your end."
```

```
[T34] AGENT | professional:3 | normal | mid | normal | (typing)
"Step two — applying the seventy-seven dollar fee waiver under courtesy code A-D-J dash courtesy. That credit posts immediately and will show on your next statement."
```

```
[T35] CUSTOMER | grateful:3 | normal | mid | normal
"Good."
```

```
[T36] AGENT | professional:3 | normal | mid | normal
"Step three — closing the savings account. Where would you like the fifteen hundred sent? ACH to your credit union, cashier's check by mail to the address on file, or transfer into your checking here as a final balance bump?"
```

```
[T37] CUSTOMER | cooperative:3 | normal | mid | normal
"ACH to the credit union. The routing and account information I gave you when I set up the external transfer last month."
```

```
[T38] AGENT | professional:3 | normal | mid | normal | (typing)
"Got it — ACH to the external account ending three-three-zero-five at Heartland Federal Credit Union. Let me also check whether there are any scheduled debits or auto-pays still tied to the savings account."
```

```
[T39] AGENT | reassuring:3 | normal | mid | normal
"No scheduled debits on savings. You're clean on that side."
```

```
[T40] CUSTOMER | satisfied:3 | normal | mid | normal
"Good. I made sure to move everything off."
```

```
[T41] AGENT | professional:3 | normal | mid | normal
"Processing the closure. Savings account closed effective today. The fifteen-hundred-dollar ACH will arrive at Heartland within one to two business days. A final statement-of-closure will be mailed to your address on file within five business days."
```

```
[T42] CUSTOMER | satisfied:3 | normal | mid | normal
"Wonderful."
```

```
[T43] AGENT | empathetic:3 | normal | mid | normal
"And I want to acknowledge — the three things you raised, the foreign transaction fee, the dormant-balance maintenance fee, the unwarned overdraft — those are real complaints about how the older products are structured. I'm logging that feedback against your account so the product team sees the pattern. Your eleven-year customer voice matters, even on the way out of one account."
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"To give you the picture of where we are — you came in to close two accounts because of cumulative fee frustration. We addressed it three ways. The checking moves to a no-fee product going forward, so the structural piece is gone. The most recent fee is waived. And savings closes cleanly with the balance returning to you. You stay a Meridian customer through the checking account, but on terms that are fair to how you actually use it."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"To summarize: checking account switched from Premium to Essentials with no maintenance fee and no minimum balance. Seventy-seven dollar fee waiver applied. Savings account closed effective today, fifteen hundred dollars ACH to your Heartland account ending three-three-zero-five within one to two business days, final statement in the mail within five business days. Does that all sound right, Ms. Salinger?"
```

```
[T46] CUSTOMER | grateful:3 | normal | mid | normal
"Yes. Karen, honestly — you handled that exactly the way I would have wanted. Most calls like this end with the bank trying to talk you out of leaving entirely. You actually listened and addressed the right things."
```

```
[T47] AGENT | warm:3 | normal | mid | normal
"That means a lot, and you're not the first customer who's said something similar to me on this kind of call. Honest listening is the only thing that works in this seat."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Salinger?"
```

```
[T49] CUSTOMER | satisfied:3 | normal | mid | normal
"No, that's everything. Thank you, Karen."
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is M-T-B dash three-three-zero-zero-nine-two-two. Because part of today's call involved a confirmed account closure, I won't send the routine post-call survey, but the case notes will reflect everything we did. Thank you for being a Meridian customer for eleven years, and thank you for staying with us on the checking side. Take care, Ms. Salinger."
```
