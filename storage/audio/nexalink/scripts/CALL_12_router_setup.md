# CALL_12 — New Router Setup Walkthrough

```yaml
call_id: CALL_12_router_setup
duration_estimate: 7m 00s
turns: 50
sop_primary: SOP-03 (Technical Support Troubleshooting)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, CS-RULE-007, CS-RULE-009, CS-RULE-010, CS-RULE-011, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 2.3 - Router Provisioning, Section 2.7 - WiFi Configuration]
customer_profile:
  name: "Gregory Halverson"
  account_number: "8052-1147-66"
  voice_hint: "male, late 50s, mild Pacific Northwest accent, patient but not tech-savvy"
agent_profile:
  name: "Marcus"
  voice_hint: "male, mid-30s, friendly neutral US accent, methodical instructional cadence"
emotional_arc: "uncertain -> engaged -> hopeful -> satisfied"
expected_outcome: "Customer connects a new NexaLink-supplied router, runs a line test, configures WiFi SSID/password, and confirms two devices online. PASS — full SOP including CS-RULE-009 re-engagement during the silent line test. No ticket required. Case ref + survey provided."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Re-engagement during silent task (line test) | T31, T33 | CS-RULE-009 — PASS (twice, both within 10s) |
| Talk-ratio balanced (avoids monologue) | T17–T25 | CS-RULE-010 — PASS (broken into steps) |
| A.C.E.S. light (mild uncertainty handled) | T15–T17 | CS-RULE-011 — PASS |
| Root cause / context explanation | T44 | CS-RULE-018 — PASS |
| Resolution summary | T46 | CS-RULE-019 — PASS |
| Anything else + case ref + survey | T48, T50 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | uncertain:3 | normal | mid | normal
"Hi Marcus, this is Greg Halverson. I just got a new router in the mail and I'm — honestly, I'm a little out of my depth here. I was hoping someone could walk me through it."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hey Greg, absolutely. That's exactly what I'm here for, and you're not the first person to feel that way about a new router. We'll get you up and running."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a new router setup, and I can certainly help you with that. Before we get into it, I'll need to verify a few details on the account — could you start with the account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure, give me a second. It's eight-zero-five-two, one-one-four-seven, six-six."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Got it. And could you confirm the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"Last four are two-two-four-zero."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And the full name on the account, exactly as it appears?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Gregory Allen Halverson."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That all matches. You're fully verified, Greg."
```

```
[T12] CUSTOMER | relieved:2 | normal | mid | normal
"Good."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Alright. Before we start unboxing anything — can you tell me the model name printed on the front of the router? Should be a short code, something like N-L six hundred or N-L gig."
```

```
[T14] CUSTOMER | concentrating:2 | normal | mid | normal | (pause)
"Let me look. It says N-L gigabit five hundred. There's a sticker on the front."
```

```
[T15] AGENT | warm:3 | normal | mid | normal
"That's exactly the one I expected, given your plan. Great. Is the unit out of the box already, or still wrapped?"
```

```
[T16] CUSTOMER | uncertain:3 | normal | mid | normal
"It's out, but I haven't plugged anything in. I wanted to talk to you first."
```

```
[T17] AGENT | reassuring:3 | normal | mid | normal
"Smart move. We'll do this in small steps. First — find the white coaxial cable that's currently going into your old modem and unplug it from the old modem. Just from the modem side, leave the wall end alone."
```

```
[T18] CUSTOMER | concentrating:2 | normal | mid | normal
"Okay, hold on… alright, it's unplugged from the old one."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"Perfect. Now take that same coax cable and screw it into the port labelled cable in on the back of the new router. The threaded silver one on the far left."
```

```
[T20] CUSTOMER | concentrating:2 | normal | mid | normal | (pause)
"Yeah, I see it. Screwing it in now… okay, that's snug."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Great. Next, plug the power adapter that came in the box into the new router and then into a wall outlet. You should see lights start to come on after a few seconds."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Done. Lights are blinking — some green, one orange."
```

```
[T23] AGENT | reassuring:3 | normal | mid | normal
"That's exactly what you should see. The orange one is the cable signal light handshaking with our network. It usually takes about ninety seconds to go solid green. Don't touch anything while it does that."
```

```
[T24] CUSTOMER | curious:3 | normal | mid | normal
"Alright. Just waiting."
```

```
[T25] AGENT | warm:3 | normal | mid | normal
"While we wait — once it's green, I'll have you log into the router admin page and set your WiFi name and password. We'll do that together."
```

```
[T26] CUSTOMER | hopeful:3 | normal | mid | normal
"Okay, sounds good."
```

```
[T27] CUSTOMER | satisfied:3 | normal | mid | normal | (pause)
"It just turned solid green."
```

```
[T28] AGENT | warm:3 | normal | mid | normal
"Excellent. That means the line is up. Let me also kick off a quick line test from my end to make sure the signal levels look healthy before we go further."
```

```
[T29] AGENT | professional:3 | normal | mid | normal | (typing)
"Running the test now."
```

```
[T30] CUSTOMER | neutral:2 | normal | mid | normal
"How long does that take?"
```

```
[T31] AGENT | warm:3 | normal | mid | normal
"About thirty seconds. I'm still here with you, Greg — the test is in progress. Thank you for your patience."
```

```
[T32] CUSTOMER | calm:2 | normal | mid | normal
"No worries."
```

```
[T33] AGENT | professional:3 | normal | mid | normal | (pause)
"Still running on my side. I'll have the result for you in just a moment."
```

```
[T34] AGENT | reassuring:3 | normal | mid | normal
"Okay, line test complete. Signal-to-noise looks clean, downstream power is well within range. The line is healthy."
```

```
[T35] CUSTOMER | relieved:3 | normal | mid | normal
"Good."
```

```
[T36] AGENT | professional:3 | normal | mid | normal
"Now, on a phone or laptop, open the WiFi list. You should see a temporary network called N-L setup with a few characters after it. Connect to that, and the password is on the bottom of the router on the same sticker as the model name."
```

```
[T37] CUSTOMER | concentrating:3 | normal | mid | normal | (pause)
"Got it… connected. It opened a page."
```

```
[T38] AGENT | warm:3 | normal | mid | normal
"That's the setup wizard. On the first screen it'll ask you to choose a WiFi network name and a password. The network name is what you'll see in the list on all your devices — make it something you'll recognize."
```

```
[T39] CUSTOMER | thoughtful:3 | normal | mid | normal
"Okay, I'll call it Halverson home, and I've got a password ready."
```

```
[T40] AGENT | reassuring:3 | normal | mid | normal
"Perfect. Type both in and tap save."
```

```
[T41] CUSTOMER | satisfied:3 | normal | mid | normal
"Done. It's saying applying settings."
```

```
[T42] AGENT | professional:3 | normal | mid | normal
"It'll reboot the WiFi for about a minute. Once you see Halverson home in your WiFi list, reconnect with the new password and you're online."
```

```
[T43] CUSTOMER | hopeful:3 | normal | mid | normal | (pause)
"Okay… there it is. I'm in. I can pull up a website."
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Beautiful. So just to give you the picture of what we did — the old modem is offline, the new router is provisioned to your account on our side, the line tested clean, and you set your own WiFi credentials so they're private to your household."
```

```
[T45] CUSTOMER | satisfied:3 | normal | mid | normal
"That was way less scary than I thought."
```

```
[T46] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you installed your new N-L gigabit five hundred router, we verified the line, you configured your WiFi name and password, and you're successfully online. The old modem can go in the prepaid return box that came with the new one and be dropped at any carrier location. Does that all sound right?"
```

```
[T47] CUSTOMER | grateful:3 | normal | mid | normal
"Sounds perfect. Thank you so much for walking me through it."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"My pleasure, Greg. Is there anything else I can help you with today?"
```

```
[T49] CUSTOMER | calm:2 | normal | mid | normal
"No, you covered it. Appreciate the patience."
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"Your case reference number is N-X-L dash one-two-zero-six-six-three-one. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Thank you for being a NexaLink customer, Greg. Take care."
```
