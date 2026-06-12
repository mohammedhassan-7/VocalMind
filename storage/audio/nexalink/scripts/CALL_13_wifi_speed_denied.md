# CALL_13 — Speed Complaint Denied (WiFi-Only Evidence)

```yaml
call_id: CALL_13_wifi_speed_denied
duration_estimate: 6m 45s
turns: 48
sop_primary: SOP-03 (Technical Support Troubleshooting)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-008, CS-RULE-011, FIN-RULE-001, FIN-RULE-002, FIN-RULE-003, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 2.8 - WiFi vs Ethernet, Section 3.3 - Compensation Matrix]
customer_profile:
  name: "Janine Pellegrini"
  account_number: "2244-9015-31"
  voice_hint: "female, late 30s, slight New York accent, frustrated and pushing for compensation"
agent_profile:
  name: "Marcus"
  voice_hint: "male, mid-30s, friendly neutral US accent, methodical instructional cadence"
emotional_arc: "frustrated -> skeptical -> cooperative -> partially_satisfied"
expected_outcome: "Customer requests a credit citing slow speeds — but evidence is WiFi-only screenshots, not a hardwired ethernet test. Marcus correctly denies the credit per FIN-RULE-003 (hardwired evidence required) and FIN-RULE-002 (subjective claims insufficient). Marcus walks her through an ethernet test on the call, finds the line is healthy, identifies WiFi interference as the likely culprit, and offers practical remediation. Customer is partially satisfied. ONE minor CS-RULE-008 slip permitted. PASS overall with minor coachable moment."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| A.C.E.S. — Acknowledge + Empathize | T15, T21 | CS-RULE-011 — PASS |
| WiFi evidence rejected per policy | T19–T23 | FIN-RULE-003 — PASS |
| Subjective claim insufficiency | T23 | FIN-RULE-002 — PASS |
| Ethernet test guided on call | T25–T31 | SOP-03 — PASS |
| FIN-RULE-001 eligibility correctly absent | T41 | PASS — no fabricated credit |
| Root cause explanation (WiFi interference) | T43 | CS-RULE-018 — PASS |
| Resolution summary | T45 | CS-RULE-019 — PASS |
| Anything else + case ref + survey | T46, T48 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | frustrated:3 | normal | mid | normal
"This is Janine Pellegrini. I am paying for a three hundred megabit plan and I am getting nowhere near that. I want a credit on my bill or I want a different plan."
```

```
[T04] AGENT | empathetic:3 | normal | mid | normal
"Hi Ms. Pellegrini, I hear you — paying for three hundred and not getting it is a frustrating situation."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a speed complaint and a possible credit, and I can certainly help you look into that. Before I can pull up the account, I'll need to verify a few details. Could you start with the account number?"
```

```
[T06] CUSTOMER | impatient:3 | normal | mid | normal
"Two-two-four-four, nine-zero-one-five, three-one."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. Could you confirm the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | impatient:2 | normal | mid | normal
"Last four are nine-five-one-eight."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And the full name on the account?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Janine Marie Pellegrini."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified."
```

```
[T12] CUSTOMER | neutral:2 | normal | mid | normal
"Okay."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"So you're on our Home Pro plan, three hundred megabits per second. Can you tell me what kind of speeds you're seeing, and how you're measuring them?"
```

```
[T14] CUSTOMER | frustrated:3 | normal | mid | normal
"I've been running speed tests on my phone, mostly Speedtest dot net, and I'm getting like forty to seventy down. Sometimes worse. I have screenshots."
```

```
[T15] AGENT | empathetic:3 | normal | mid | normal
"Forty to seventy on a three hundred plan is well under what you should be seeing, and I completely understand why you'd want that addressed. Let me ask one important clarifying question, because it makes a real difference."
```

```
[T16] CUSTOMER | skeptical:3 | normal | mid | normal
"Okay."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"Were those speed tests done while connected over WiFi, or were they on a device that was plugged directly into the router with an ethernet cable?"
```

```
[T18] CUSTOMER | frustrated:3 | normal | mid | normal
"WiFi. I don't have an ethernet cable for my phone."
```

```
[T19] AGENT | thoughtful:3 | normal | mid | normal
"That's the part I need to be transparent with you about. For a service credit based on speed, our refund policy specifically requires the evidence to come from a hardwired ethernet test, not WiFi."
```

```
[T20] CUSTOMER | frustrated:4 | normal | mid | normal
"Are you serious? So my speed tests don't count because I used WiFi like every normal person?"
```

```
[T21] AGENT | empathetic:3 | normal | mid | normal
"I hear how that sounds, and the reason is real even if it's frustrating. WiFi adds variables we can't measure or fix from the network side — distance from the router, walls, neighbours' networks on the same channel, the device's own radio quality."
```

```
[T22] CUSTOMER | skeptical:3 | normal | mid | normal
"Mm-hm."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"So an ethernet test isolates the line from the WiFi. If the ethernet test also shows under half of plan, that's a confirmed line issue and we can talk about credit, downgrade, or contract exit. If the ethernet test shows close to three hundred, then the line is doing what you paid for and the problem is in the WiFi layer — which is fixable but isn't a billing credit issue."
```

```
[T24] CUSTOMER | frustrated:3 | normal | mid | normal
"Fine. Whatever. So how do we do an ethernet test."
```

```
[T25] AGENT | warm:3 | normal | mid | normal
"That's the right move. I'd rather do this together right now than have you go away guessing. Do you have a laptop or desktop computer with an ethernet port?"
```

```
[T26] CUSTOMER | cooperative:3 | normal | mid | normal
"I have a laptop. And there was an ethernet cable in the box when the router came."
```

```
[T27] AGENT | reassuring:3 | normal | mid | normal
"Perfect. So plug one end of that ethernet cable into the back of the router, into any of the yellow LAN ports, and the other end directly into your laptop. Turn the WiFi off on the laptop so we know we're testing the wired line and not falling back to WiFi."
```

```
[T28] CUSTOMER | concentrating:2 | normal | mid | normal | (pause)
"Okay, hold on… plugging it in… and WiFi is off. The icon shows wired connection."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Great. Now open the browser and go to Speedtest dot net, hit go, and tell me what numbers come up — both download and upload."
```

```
[T30] CUSTOMER | concentrating:3 | normal | mid | normal | (pause)
"It's running… okay. Two hundred and eighty-six down, eleven up."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"That's the answer. Two hundred and eighty-six down on a three hundred plan is well within range — most plans don't hit perfect peak because of normal overhead, but two-eighty-six is the line doing its job."
```

```
[T32] CUSTOMER | confused:3 | normal | mid | normal
"So why am I getting forty over WiFi?"
```

```
[T33] AGENT | thoughtful:3 | normal | mid | normal
"Almost certainly WiFi interference or distance. A few quick questions — where in the house is the router, and where are you usually using your phone?"
```

```
[T34] CUSTOMER | thoughtful:3 | normal | mid | normal
"The router is in the basement closet where the cable comes in. I'm usually upstairs in the living room, two floors up. There's a thick floor in between."
```

```
[T35] AGENT | reassuring:3 | normal | mid | normal
"That's almost certainly it. Two floors of concrete or thick wood absorbs WiFi very heavily, especially the five-gigahertz band that gives you the higher speeds. The signal that's reaching your phone upstairs is a small fraction of what's coming out of the router."
```

```
[T36] CUSTOMER | curious:3 | normal | mid | normal
"So what do I do about it?"
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"Two practical options. One — move the router up to a central location on the main floor if the cable run can support that, which often it can. Two — add a mesh extender so you have a second WiFi point on the living-room floor. Either will give you a real boost. Our equipment team can help with either."
```

```
[T38] CUSTOMER | thoughtful:3 | normal | mid | normal
"How much is a mesh extender from you guys?"
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"It's a five dollar per month equipment line on the bill, no upfront. Or you can buy a third-party one and use it with our network — your choice. Either works."
```

```
[T40] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay. That actually makes sense. So just to confirm — no credit."
```

```
[T41] AGENT | empathetic:3 | normal | mid | normal
"That's right. Because the hardwired test confirmed the line is doing what you pay for, there isn't a service credit available in this case. I know that's not the answer you wanted, but I'd rather give you the real picture than apply a credit that wouldn't actually fix the experience."
```

```
[T42] CUSTOMER | resigned:3 | normal | mid | normal
"Yeah, fair enough."
```

```
[T43] AGENT | warm:3 | normal | mid | normal
"And just so you have the full picture — the root cause here is WiFi range, not the line. The line is healthy. So whatever route you take with the extender or moving the router, the speed will follow."
```

```
[T44] CUSTOMER | satisfied:3 | normal | mid | normal
"Got it. That helps."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported slow WiFi speeds, we ran a hardwired ethernet test which confirmed two-eighty-six on a three hundred plan, the line is performing as expected, no service credit applies, and the likely fix is either repositioning the router or adding a mesh extender. I'm leaving the case open so equipment team can follow up on the extender option if you'd like. Does that all sound right?"
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Ms. Pellegrini?"
```

```
[T47] CUSTOMER | calm:2 | normal | mid | normal
"No, that's it. Thanks for actually explaining it."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is N-X-L dash one-three-four-four-nine-zero-two. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Thank you for being a NexaLink customer."
```
