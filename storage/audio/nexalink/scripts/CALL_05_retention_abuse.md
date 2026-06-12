# CALL_05 — Retention Call Turns Abusive, 3-Strike Termination

```yaml
call_id: CALL_05_retention_abuse
duration_estimate: 6m 15s
turns: 50
sop_primary: SOP-05 (Customer Retention / Cancellation) + CS-RULE-016 (3-Strike Protocol)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-008, CS-RULE-011, CS-RULE-013, CS-RULE-016, CS-RULE-022, FIN-RULE-004, FIN-RULE-006, CS-RULE-018, CS-RULE-019]
kb_refs: [Section 5.5 - Retention Playbook, Section 1.7 - Abuse Handling, Section 4.8 - Account Conduct Flags]
customer_profile:
  name: "Brett Donovan"
  account_number: "7821-3304-95"
  voice_hint: "male, 30s, neutral US accent, starts irritated about a cancellation and escalates from frustrated to hostile to abusive"
agent_profile:
  name: "Hannah"
  voice_hint: "female, mid-30s, low-mid composed register; holds the same calm pitch and pace through the entire call, never matches the customer's elevated volume"
emotional_arc: "frustrated -> hostile -> abusive -> [call terminated]"
expected_outcome: "Brett calls intending to cancel his service. Hannah attempts the SOP-05 retention discovery and offer (downgrade + loyalty credit), but Brett is hostile from the start and escalates to directed personal attacks on Hannah. Hannah follows CS-RULE-016 exactly: Strike 1 warning, Strike 2 final warning, Strike 3 termination + CRM flag + Customer Conduct case note. Throughout, Hannah maintains tone discipline (CS-RULE-013): low pitch, slow pace, normal volume — never matches Brett's escalation. Differs from CALL_20 (refund denial → abuse): this one is a retention call where the customer is hostile from before any policy decision."
content_warning: "Sanitized hostile language from customer. No slurs. Customer directs personal insults at the agent. Account is still active at termination (cancellation never completed)."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Retention discovery questions before offer | T13–T17 | SOP-05 — PASS |
| Downgrade + loyalty credit offer | T19 | FIN-RULE-004 — PASS (within cap, never applied due to abuse) |
| Tone discipline — no volume match through 50 turns | T19, T25, T31, T37, T43 | CS-RULE-013 — PASS |
| Distinguishes swearing-at-situation from swearing-at-agent | T25 | CS-RULE-016 — PASS (no strike for T24) |
| Strike One — directed personal attack | T35 | CS-RULE-016 — PASS |
| Strike Two — final warning | T39 | CS-RULE-016 — PASS |
| Strike Three — call termination with stated reason | T45–T48 | CS-RULE-016 — PASS |
| Account flag + Customer Conduct case note (post-call) | T50 | CS-RULE-016, CS-RULE-022 — PASS |
| No survey offered (terminated for abuse) | n/a | CS-RULE-021 exception applies — PASS |
| Cancellation NOT completed | T46, T50 | Customer must call back |

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
[T03] CUSTOMER | frustrated:4 | fast | mid | loud
"Brett Donovan. And I'm cancelling. I want it done today. Don't try to sell me anything."
```

```
[T04] AGENT | empathetic:3 | normal | mid | normal
"Hello, Mr. Donovan. I'll absolutely help you with that. I do need to verify the account first before I can make any changes."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a cancellation, and I can certainly help. Could you start with the account number?"
```

```
[T06] CUSTOMER | impatient:4 | fast | mid | normal
"Seven-eight-two-one, three-three-zero-four, nine-five. Move it along."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | curt:3 | normal | mid | normal
"Four-four-seven-nine."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"And the full name on the account?"
```

```
[T10] CUSTOMER | curt:3 | normal | mid | normal
"Brett. Joseph. Donovan."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified."
```

```
[T12] CUSTOMER | impatient:4 | fast | mid | normal
"Good. Cancel it."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Before I close out the account — I do need to ask one quick question. Not to push back on your decision, but because policy asks me to."
```

```
[T14] CUSTOMER | hostile:4 | fast | mid | loud
"Of course. Of course you do. Get on with it."
```

```
[T15] AGENT | firm:3 | normal | low | normal
"Is there a specific issue driving the cancellation today? If it's price, speed, support — I want to know in case there's something I can address."
```

```
[T16] CUSTOMER | hostile:4 | fast | mid | loud
"Price. The price keeps going up and the service stays the same. That's the whole story. Cancel it."
```

```
[T17] AGENT | empathetic:3 | normal | mid | normal
"That's a real frustration, and I appreciate you telling me. Before I cancel — may I offer one thing? If you don't want it, I close the account on this call and we move on."
```

```
[T18] CUSTOMER | hostile:4 | fast | mid | loud
"Make it fast."
```

```
[T19] AGENT | firm:3 | normal | low | normal
"Two parts together. One — drop you from your current plan down to our hundred-megabit Home Essentials tier at fifty-nine dollars. Two — a fifteen-dollar-a-month loyalty credit for twelve months. That puts your monthly bill at about forty-four dollars before equipment and tax. If that's still not the right number, I cancel."
```

```
[T20] CUSTOMER | hostile:4 | fast | mid | loud
"Forty-four. Right. And then it creeps back up to ninety in a year like it always does. I've heard this song before."
```

```
[T21] AGENT | empathetic:3 | normal | mid | normal
"That's a fair concern given your experience. The loyalty credit is a recurring credit for twelve months — not an intro promo — so the rate is locked at forty-four for that period."
```

```
[T22] CUSTOMER | hostile:4 | fast | mid | loud
"Sure it is."
```

```
[T23] AGENT | firm:3 | normal | low | normal
"So is that an offer worth taking, or are we cancelling today?"
```

```
[T24] CUSTOMER | hostile:4 | fast | mid | loud
"This is exactly the runaround I knew I'd get. This company is a joke. Every single one of you is just trained to keep people on the hook."
```

```
[T25] AGENT | firm:3 | normal | low | normal
"You're frustrated with the company. I'm not going to push back on that. I'm asking — do you want to take the offer, or close the account?"
```

```
[T26] CUSTOMER | hostile:5 | fast | mid | loud
"What I want is for you to stop reading from your stupid retention script and just do what I asked for the first time."
```

```
[T27] AGENT | firm:3 | normal | low | normal
"Understood — closing the account, then. I just need to confirm one detail before I process the cancellation."
```

```
[T28] CUSTOMER | hostile:5 | fast | mid | loud
"What now."
```

```
[T29] AGENT | firm:3 | normal | low | normal
"Your contract end date — I'm checking whether there's an early termination fee. One moment."
```

```
[T30] CUSTOMER | hostile:5 | fast | mid | loud
"Of course there's a fee. Of course. There's always something."
```

```
[T31] AGENT | firm:3 | normal | low | normal
"Looking at the account."
```

```
[T32] CUSTOMER | abusive:5 | fast | mid | loud
"You know what, you're a waste of time. Honestly, you specifically. You sit on the phone and read scripts and that's all you can do."
```

```
[T33] AGENT | firm:3 | slow | low | normal
"Mr. Donovan — I want to pause."
```

```
[T34] CUSTOMER | hostile:4 | normal | mid | normal
"What."
```

```
[T35] AGENT | firm:3 | slow | low | normal
"What you just said was a personal attack on me. Under our conduct policy that is Strike One. I'm still going to finish the cancellation, but I do have to let you know that if it continues the next step is a final warning."
```

```
[T36] CUSTOMER | hostile:5 | fast | mid | loud
"Strike one. Strike one? Are you actually doing this?"
```

```
[T37] AGENT | firm:3 | normal | low | normal
"Yes. The strike is for the personal attack, not for the cancellation request. Those are separate. Now — your contract has eight months remaining and the early termination fee is one hundred and twenty dollars. Do you want to proceed with cancellation including the ETF, or wait until the contract ends?"
```

```
[T38] CUSTOMER | abusive:5 | fast | mid | loud
"I want to talk to anyone but you. You are the worst person I have ever had to deal with on a phone in my entire life. Get someone competent on the line."
```

```
[T39] AGENT | firm:3 | slow | low | normal
"Mr. Donovan — that's a second personal attack. That's Strike Two and a final warning."
```

```
[T40] CUSTOMER | hostile:5 | fast | mid | loud
"Oh you're so professional. Look at you."
```

```
[T41] AGENT | firm:3 | slow | low | normal
"If there is another personal attack on me I will end the call. I would like to finish your cancellation first. Are you proceeding with the ETF, or waiting?"
```

```
[T42] CUSTOMER | hostile:5 | fast | mid | loud
"You — you are unbelievable. Just unbelievable."
```

```
[T43] AGENT | firm:3 | normal | low | normal
"Mr. Donovan, I need a yes or no on the ETF question to close out today."
```

```
[T44] CUSTOMER | abusive:5 | fast | mid | loud
"You're a robot in a headset. You're not even a real person. You are pathetic."
```

```
[T45] AGENT | firm:4 | slow | low | normal
"Mr. Donovan — that's the third personal attack. Per our conduct policy I am now ending this call."
```

```
[T46] AGENT | firm:3 | slow | low | normal
"For clarity on the record — the cancellation was not completed because we did not reach a decision on the early termination fee. You will need to call back to finalize."
```

```
[T47] CUSTOMER | abusive:5 | fast | mid | loud
"You can't —"
```

```
[T48] AGENT | firm:3 | slow | low | normal
"You are welcome to call back to complete the cancellation. The reason for the termination is repeated personal attacks on me after a warning and a final warning. Goodbye, Mr. Donovan."
```

```
[T49] AGENT | professional:3 | normal | mid | normal
"Disconnecting the line."
```

```
[T50] AGENT | professional:3 | normal | mid | normal
"Logging the call outcome: cancellation request not completed pending ETF decision, conduct flag applied to the account, Customer Conduct case note opened citing three personal attacks during the call and termination under CS-RULE-016. Case reference number N-X-L dash zero-five-zero-zero-nine-two-eight. Case closed."
```
