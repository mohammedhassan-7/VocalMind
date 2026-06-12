# CALL_14 — Missed Technician Appointment (1st Occurrence)

```yaml
call_id: CALL_14_missed_appointment
duration_estimate: 6m 30s
turns: 46
sop_primary: SOP-03 (Technical Support Troubleshooting) + SOP-02 (Compensation)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-011, CS-RULE-014, CS-RULE-015, FIN-RULE-004, FIN-RULE-006, FIN-RULE-010, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.3 - Compensation Matrix, Section 4.1 - Dispatch Operations]
customer_profile:
  name: "Rebecca Caldwell"
  account_number: "5587-2106-94"
  voice_hint: "female, late 30s, neutral US accent, irritated about wasted day"
agent_profile:
  name: "Marcus"
  voice_hint: "male, mid-30s, friendly neutral US accent, methodical instructional cadence"
emotional_arc: "frustrated -> acknowledged -> partially_satisfied -> grateful"
expected_outcome: "Customer waited home all morning for an installation technician who never arrived. Marcus correctly applies the $25 missed-appointment credit per the compensation matrix (1st occurrence), validates the courtesy-credit anti-fraud rule (FIN-RULE-006 within-180-days check), and opens a Field Service ticket to reschedule with priority. Within agent cap ($25 ≤ $200). PASS — full SOP."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| A.C.E.S. — full sequence | T15–T19 | CS-RULE-011 — PASS |
| Compensation matrix — $25 missed appointment 1st occurrence | T21–T23 | PASS |
| Authorization within cap | T25 | FIN-RULE-004 ($25 ≤ $200) — PASS |
| FIN-RULE-006 180-day courtesy-credit check | T21 | PASS (none in window) |
| Field Service ticket + reschedule SLA | T30–T34 | CS-RULE-014, CS-RULE-015 — PASS |
| Refund timeline verbatim | T38 | FIN-RULE-010 — PASS (bill credit script used) |
| Root cause + resolution summary | T41–T43 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T44, T46 | CS-RULE-020, CS-RULE-021 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Marcus. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"And this call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | frustrated:4 | normal | mid | normal
"This is Rebecca Caldwell. I waited home all morning for a technician who was supposed to be at my house between eight and noon, and nobody ever came. Nobody called. Nothing."
```

```
[T04] AGENT | empathetic:4 | normal | mid | normal
"Ms. Caldwell, I am so sorry. Waiting a full morning for an appointment that doesn't show is genuinely frustrating, and I completely understand why you're upset."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a missed technician appointment, and I can certainly help you with that. Before I pull up the work order, I'll need to verify a few details — could you start with the account number?"
```

```
[T06] CUSTOMER | impatient:3 | normal | mid | normal
"Five-five-eight-seven, two-one-zero-six, nine-four."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thanks. And the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"Six-six-one-nine."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"And the full name on the account?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Rebecca Lynn Caldwell."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified, Ms. Caldwell."
```

```
[T12] CUSTOMER | impatient:3 | normal | mid | normal
"Okay, so what happened?"
```

```
[T13] AGENT | professional:3 | normal | mid | normal | (typing)
"Let me pull up the work order now."
```

```
[T14] AGENT | professional:3 | normal | mid | normal
"Yes — I can see the appointment, work order ending five-two-one-eight, scheduled for today, eight AM to noon window, address matches your account. Let me check the dispatch status."
```

```
[T15] AGENT | concerned:3 | normal | mid | normal
"I see what happened, and I'm sorry. The tech assigned to your job was reassigned this morning to an emergency line repair in another neighbourhood. The reassignment didn't trigger the customer notification it should have, so you weren't told."
```

```
[T16] CUSTOMER | frustrated:4 | normal | mid | normal
"So you're telling me nobody bothered to call me and let me know? I rearranged my whole day for this."
```

```
[T17] AGENT | empathetic:4 | normal | mid | normal
"You're absolutely right to be upset. The notification not going out is on us — not on you — and it shouldn't have happened. I want to acknowledge that fully."
```

```
[T18] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Thank you for at least saying that."
```

```
[T19] AGENT | reassuring:3 | normal | mid | normal
"Let me clarify what we can do, then I'd like to solve it on this call. There's compensation policy for a missed appointment, and there's the reschedule itself. I'll cover both."
```

```
[T20] CUSTOMER | neutral:2 | normal | mid | normal
"Okay."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"For a first missed appointment our compensation matrix is a twenty-five dollar account credit. If this had been a repeat occurrence it would be fifty dollars plus a priority reschedule, but I'm checking your history and I'm not seeing any prior missed visits or other courtesy credits in the last six months."
```

```
[T22] CUSTOMER | curious:3 | normal | mid | normal
"It's the first one."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"That matches what I'm seeing on my end. So it's the twenty-five dollar credit, and I'll request a priority reschedule even though that's normally for repeats — given how it played out today."
```

```
[T24] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay, that's fair."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"I'll process the credit first. Twenty-five dollars, courtesy credit code — within my agent authorization, so I can apply it directly on this call."
```

```
[T26] CUSTOMER | neutral:2 | normal | mid | normal
"Okay."
```

```
[T27] AGENT | professional:3 | normal | mid | normal | (typing)
"Running the authorization check and applying it now."
```

```
[T28] AGENT | reassuring:3 | normal | mid | normal
"Done. Twenty-five dollar credit posted to your account under courtesy code A-D-J dash courtesy."
```

```
[T29] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T30] AGENT | professional:3 | normal | mid | normal
"For the reschedule — I'm opening a Field Service ticket right now to get you back on the dispatch board with priority flagged. What days and times generally work best for you in the next week?"
```

```
[T31] CUSTOMER | thoughtful:3 | normal | mid | normal
"I work from home Tuesday and Thursday. Tuesday morning would be best. Not eight to noon again, though — please."
```

```
[T32] AGENT | warm:3 | normal | mid | normal
"Completely understand. Let me see — I have a nine to eleven AM slot Tuesday available, which is a tighter window than today's. Would that work?"
```

```
[T33] CUSTOMER | satisfied:3 | normal | mid | normal
"Yes. That's much better."
```

```
[T34] AGENT | professional:3 | normal | mid | normal
"Booking it now. Tuesday, nine to eleven AM, same address, priority flag on the work order. The dispatch team will follow up with confirmation and the tech's contact info within the next four hours."
```

```
[T35] CUSTOMER | cooperative:3 | normal | mid | normal
"Four hours. Got it."
```

```
[T36] AGENT | reassuring:3 | normal | mid | normal
"And on Tuesday morning, the tech will call you about thirty minutes out so you have notice. If anything changes on our end before then, you will be notified directly — that won't happen twice."
```

```
[T37] CUSTOMER | curious:3 | normal | mid | normal
"And the credit — when does that actually show on my bill?"
```

```
[T38] AGENT | professional:3 | normal | mid | normal
"The balance on your online account will update within five days but will officially appear on your next PDF bill."
```

```
[T39] CUSTOMER | satisfied:3 | normal | mid | normal
"Okay, perfect."
```

```
[T40] AGENT | empathetic:3 | normal | mid | normal
"And again — I really am sorry for how today went. That's not the experience we want anyone walking away with."
```

```
[T41] AGENT | warm:3 | normal | mid | normal
"To give you the full picture — the root cause was an internal dispatch reassignment that didn't fire the customer notification it was supposed to. I'm logging that on the work order so the operations team can investigate the notification gap on their end."
```

```
[T42] CUSTOMER | grateful:3 | normal | mid | normal
"I appreciate you actually looking into the why."
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"To summarize: today's eight to noon technician appointment was missed because of an internal reassignment with no customer notification, I've applied a twenty-five dollar account credit, I've rebooked you for Tuesday nine to eleven AM with priority flagged, and dispatch will confirm within four hours. Does that all sound right?"
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Caldwell?"
```

```
[T45] CUSTOMER | grateful:3 | normal | mid | normal
"No, that more than covers it. Thank you for handling it well."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is N-X-L dash one-four-eight-one-zero-five-six. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Thank you for being a NexaLink customer, Ms. Caldwell. Have a much better rest of your day."
```
