# CALL_19 — Verified Slow Speed → ETF Waiver via Manager Ticket

```yaml
call_id: CALL_19_speed_downgrade_etf_waiver
duration_estimate: 7m 15s
turns: 52
sop_primary: SOP-05 (Cancellation) + SOP-03 (Speed Verification) + SOP-02 (Compensation)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-011, CS-RULE-014, CS-RULE-015, FIN-RULE-001, FIN-RULE-003, FIN-RULE-004, FIN-RULE-005, FIN-RULE-010, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.3 - Compensation Matrix, Section 5.6 - ETF Waiver Process]
customer_profile:
  name: "Camille Beaufort"
  account_number: "4493-7728-66"
  voice_hint: "female, late 40s, slight Louisiana accent, fed up but procedural"
agent_profile:
  name: "Hannah"
  voice_hint: "female, mid-30s, low-mid composed register, calm and steady"
emotional_arc: "frustrated -> validated -> cooperative -> resolved"
expected_outcome: "Customer is locked into a 24-month contract. Hardwired ethernet test shows speeds at 38% of advertised plan. Hannah verifies the slow-speed evidence per FIN-RULE-003 (hardwired ethernet), then offers two policy-compliant outcomes per the FIN compensation matrix: retroactive downgrade OR ETF-waived contract exit. Customer chooses ETF-waived exit. Because the ETF waiver is an out-of-policy override requiring Manager Approval, Hannah opens a Manager Approval ticket per FIN-RULE-005 instead of promising the waiver outright. PASS — full SOP."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| A.C.E.S. — full sequence | T15–T21 | CS-RULE-011 — PASS |
| Hardwired ethernet test guided on call | T17–T24 | FIN-RULE-003 — PASS |
| FIN-RULE-001 cat. 3 eligibility (< 50% of plan verified) | T26 | PASS |
| Both compensation-matrix options offered | T29, T31 | PASS |
| Does NOT promise ETF waiver before authorization | T37 | FIN-RULE-005 — PASS |
| Manager Approval ticket for ETF waiver | T39, T46 | FIN-RULE-004/005, CS-RULE-014 — PASS |
| Ticket SLA (1 business day) communicated | T39, T41 | CS-RULE-015 — PASS |
| Refund timeline verbatim | T43 | FIN-RULE-010 — PASS |
| Root cause + resolution summary | T49 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T50, T52 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | frustrated:3 | normal | mid | normal
"This is Camille Beaufort. I have had it. I'm paying for a three hundred megabit plan, the speeds are nowhere near that, and your contract has me locked in for another fourteen months. So I want to know what we are going to do about this."
```

```
[T04] AGENT | empathetic:4 | normal | mid | normal
"Ms. Beaufort, I hear you, and being locked into a contract for service that isn't performing is exactly the kind of situation we have specific policy for. Let me work through this with you."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about consistently slow speeds on your plan and the contract obligation. I can certainly help you with that. Before I look at the account, I'll need to verify a few details — could you start with the account number?"
```

```
[T06] CUSTOMER | impatient:3 | normal | mid | normal
"Four-four-nine-three, seven-seven-two-eight, six-six."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"Two-zero-eight-nine."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"And the full name on the account, exactly as it appears?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Camille Antoinette Beaufort."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified."
```

```
[T12] CUSTOMER | impatient:3 | normal | mid | normal
"Good. Let's get to it."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"I can see you're on Home Pro, three hundred megabits, contract started ten months ago. Twenty-four-month term, so fourteen months remaining. Standard early termination fee on that contract is one hundred and twenty dollars if cancelled today. That's the picture."
```

```
[T14] CUSTOMER | frustrated:4 | normal | mid | normal
"Right, that's the problem. One twenty for cancelling service that doesn't work."
```

```
[T15] AGENT | empathetic:3 | normal | mid | normal
"Completely understand the frustration of that math. Before we talk about exit, I need to verify the speed claim using the policy's accepted method — a hardwired ethernet test. WiFi tests don't count for this kind of decision, no matter what they show, because too many variables sit between the line and the WiFi device."
```

```
[T16] CUSTOMER | frustrated:3 | normal | mid | normal
"I know about the ethernet thing. I read your terms when I signed up. I have a cable ready. Tell me what to do."
```

```
[T17] AGENT | warm:3 | normal | mid | normal
"That's perfect — having you ready saves us time. Do you have a laptop or desktop with an ethernet port and the cable already?"
```

```
[T18] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. Cable from router to laptop. WiFi is off on the laptop."
```

```
[T19] AGENT | reassuring:3 | normal | mid | normal
"Then we are in great shape. Open Speedtest dot net in your browser, hit go, and tell me the download and upload numbers."
```

```
[T20] CUSTOMER | concentrating:3 | normal | mid | normal | (pause)
"Running… okay. One hundred and fourteen down. Six up."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Thank you. Let me run it again from my side to confirm — sometimes the first run is unrepresentative."
```

```
[T22] CUSTOMER | curious:3 | normal | mid | normal
"Okay."
```

```
[T23] AGENT | professional:3 | normal | mid | normal | (typing)
"Run two — one moment."
```

```
[T24] AGENT | concerned:3 | normal | mid | normal
"Run two on my side shows one hundred and nine down. Average of the two is one-eleven-and-a-half down on a three hundred megabit plan."
```

```
[T25] CUSTOMER | vindicated:3 | normal | mid | normal
"Right. Like I said."
```

```
[T26] AGENT | professional:3 | normal | mid | normal
"That's confirmed. One-eleven on three hundred is just under thirty-eight percent of plan, well below the fifty percent threshold. Under our policy, that meets the eligibility for refund or contract action."
```

```
[T27] CUSTOMER | curious:3 | normal | mid | normal
"What are my options exactly?"
```

```
[T28] AGENT | professional:3 | normal | mid | normal
"Two policy-compliant options."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Option one — retroactive plan downgrade. We drop you from the three hundred plan down to the one hundred megabit tier, backdated to the date you first reported the issue. That's effectively crediting you the price difference for the months you've been underserved, and going forward you pay the lower price for what you've actually been getting."
```

```
[T30] CUSTOMER | thoughtful:3 | normal | mid | normal
"Hm."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"Option two — contract exit without early termination fee. We waive the one twenty ETF and you're free to leave the service entirely. The waiver isn't automatic; it requires Manager Approval because it's outside my single-call authorization, but the policy clearly supports it given the verified evidence."
```

```
[T32] CUSTOMER | thoughtful:3 | normal | mid | normal
"Either is on the table?"
```

```
[T33] AGENT | reassuring:3 | normal | mid | normal
"Either is on the table — this is your choice, not mine. The first is appropriate if you actually want the internet and just need fair pricing for what's reaching you. The second is appropriate if you want to leave entirely and find another provider."
```

```
[T34] CUSTOMER | thoughtful:3 | normal | mid | normal
"Honestly? I want out. I've already been looking at other providers. I'd rather just close this and move."
```

```
[T35] AGENT | warm:3 | normal | mid | normal
"That's a completely reasonable choice given what we just confirmed."
```

```
[T36] CUSTOMER | cooperative:3 | normal | mid | normal
"So how does that work?"
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"Here's exactly how I'm going to handle it, and I want to be transparent — I'm not going to promise you a waived ETF before authorization confirms it, because that's a policy I follow precisely so customers aren't told one thing and then surprised."
```

```
[T38] CUSTOMER | cooperative:3 | normal | mid | normal
"Fair."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"What I am going to do is open a Manager Approval ticket on this call, with the two ethernet test results, the speed-versus-plan ratio, and your stated preference for the contract exit option. Manager Approval will return a decision within one business day. Given that the evidence is verified and within policy, the expected outcome is approval — but the decision is theirs, not mine, and you'll hear it directly from them."
```

```
[T40] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"One business day."
```

```
[T41] AGENT | professional:3 | normal | mid | normal
"One business day. They'll call the phone number on file. If approved, the ETF is waived, your account closes effective the date you choose, and a prepaid equipment return label is emailed to you the same day. The standard refund of any prepaid balance follows our normal timeline."
```

```
[T42] CUSTOMER | curious:3 | normal | mid | normal
"What does that timeline look like?"
```

```
[T43] AGENT | professional:3 | normal | mid | normal
"We have processed the refund today, but depending on your bank it may take one to two billing cycles to appear."
```

```
[T44] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay. And if Manager Approval declines?"
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"Then option one — the retroactive downgrade — is still available to you as a fallback, and that one I can do on the call myself. So you're not without a path either way."
```

```
[T46] AGENT | professional:3 | normal | mid | normal | (typing)
"Opening the Manager Approval ticket with all the verified evidence attached."
```

```
[T47] CUSTOMER | cooperative:3 | normal | mid | normal
"Good."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"And I want to acknowledge — you came in frustrated, you were right to be, the numbers backed you up, and now there's a clear path. That's the way these calls should go."
```

```
[T49] AGENT | reassuring:3 | normal | mid | normal
"To summarize: we ran two hardwired ethernet tests and confirmed your line at thirty-eight percent of advertised plan. You chose the contract-exit-with-ETF-waived option, I opened a Manager Approval ticket with all the verified evidence and your stated preference, and you'll receive a decision within one business day by phone. If approved, account closes and equipment returns the same day. If declined, retroactive downgrade remains available. Does that all sound right?"
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Beaufort?"
```

```
[T51] CUSTOMER | grateful:3 | normal | mid | normal
"No, you handled that better than I expected. Thank you, Hannah."
```

```
[T52] AGENT | warm:3 | normal | mid | normal
"Thank you for the kind words. Your case reference number is N-X-L dash one-nine-four-four-eight-two-seven. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Take care."
```
