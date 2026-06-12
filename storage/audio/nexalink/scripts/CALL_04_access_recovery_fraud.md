# CALL_04 — Suspected Unauthorized Access (Elderly Customer)

```yaml
call_id: CALL_04_access_recovery_fraud
duration_estimate: 7m 30s
turns: 52
sop_primary: SOP-04 (Account Access Recovery) + SOP-02 (Security Response)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, CS-RULE-009, CS-RULE-011, CS-RULE-013, CS-RULE-014, CS-RULE-015, SEC-RULE-001, SEC-RULE-002, SEC-RULE-006, SEC-RULE-007, SEC-RULE-008, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 4.5 - Suspected Unauthorized Access, Section 4.7 - Account Freeze Procedure]
customer_profile:
  name: "Margaret Holloway"
  account_number: "1185-6602-44"
  voice_hint: "female, late 60s, neutral US accent with a soft natural tremor that grows under stress; speaks slower than baseline"
agent_profile:
  name: "Aisha"
  voice_hint: "female, late 30s, warm low-mid register, deliberate and reassuring; speaks slower than her usual pace for this caller"
emotional_arc: "worried -> afraid -> tearful -> relieved"
expected_outcome: "Margaret Holloway, an elderly customer, noticed a $240 charge she didn't make and is genuinely frightened that her account has been compromised. Aisha takes extra time with her (slower pace, gentler check-ins), completes 3-of-5 verification, then executes the full SEC-RULE-008 procedure: (1) freeze, (2) Security Review flag, (3) Data Compliance ticket with 72-hr SLA, (4) password-change advice in clear, step-by-step language. Aisha also opens a Fraud Investigation ticket for the disputed charge per FIN-RULE-008 (no refund before investigation). PASS — full SOP, tone-discipline exemplary."
content_warning: "Elderly customer becomes briefly tearful from fear. No abuse."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002, SEC-RULE-001 — PASS |
| Acknowledge reason for call | T07 | CS-RULE-003 — PASS |
| 3-of-5 verification | T08–T13 | account number + last 4 + name — PASS |
| Tone adapted to vulnerable customer (slower, lower) | T04, T17, T21 | CS-RULE-013 — PASS |
| A.C.E.S. — full sequence | T17–T23 | CS-RULE-011 — PASS |
| Re-engagement during silent task | T36 | CS-RULE-009 — PASS |
| Privacy data-use statement | T19 | SEC-RULE-002 — PASS |
| SEC-RULE-008 (1) freeze | T23–T25 | PASS |
| SEC-RULE-008 (2) Security Review flag | T27 | PASS |
| SEC-RULE-008 (3) Data Compliance ticket, 72-hr SLA | T33 | PASS |
| SEC-RULE-008 (4) password-change advice (step-by-step) | T39–T45 | PASS |
| Fraud Investigation ticket for disputed charge | T29 | FIN-RULE-008 — PASS |
| Does NOT issue refund before investigation | T29 | FIN-RULE-008 — PASS |
| Root cause + resolution summary | T48–T49 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T51, T52 | CS-RULE-020, CS-RULE-021 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Aisha. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"And this call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | worried:4 | slow | mid | quiet
"Hello, Aisha. My name is Margaret Holloway. I am sorry to bother you, but I think — I think something might be wrong with my account."
```

```
[T04] AGENT | empathetic:4 | slow | mid | normal
"Hello Ms. Holloway. You're not bothering me at all — I'm here to help. Take your time and tell me what you noticed."
```

```
[T05] CUSTOMER | worried:4 | slow | mid | normal
"There's a charge on my bill, two hundred and forty dollars. I have never seen it before. And I — I don't recognize what it is for. I'm worried someone may have done something to my account."
```

```
[T06] AGENT | empathetic:4 | slow | mid | normal
"Thank you for calling us right away — that's exactly what you should do when something looks off. I'm going to help you through this step by step, and there's no rush. You're safe with me on the line."
```

```
[T07] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a charge you don't recognize, and possibly account security. I can certainly help with both. Before I look at anything, I'll need to verify your identity. Could you start with your account number?"
```

```
[T08] CUSTOMER | thoughtful:2 | slow | mid | normal | (pause)
"Yes — let me find it… one-one-eight-five, six-six-zero-two, four-four."
```

```
[T09] AGENT | reassuring:3 | normal | mid | normal
"Wonderful. And could you confirm the last four digits of the payment method on file?"
```

```
[T10] CUSTOMER | thoughtful:3 | slow | mid | normal
"That should be the card ending in eight-zero-seven-one."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"Perfect, that matches. And finally — could you confirm the full name on the account?"
```

```
[T12] CUSTOMER | cooperative:3 | slow | mid | normal
"Margaret Eleanor Holloway."
```

```
[T13] AGENT | reassuring:3 | normal | mid | normal
"Thank you, Ms. Holloway. You're fully verified."
```

```
[T14] CUSTOMER | relieved:2 | normal | mid | normal
"Oh, good."
```

```
[T15] AGENT | warm:3 | normal | mid | normal
"Before we go any further, I want to tell you what I'm going to do — and the order I'm going to do it in — so nothing on the account changes without you knowing first."
```

```
[T16] CUSTOMER | cooperative:3 | slow | mid | normal
"Yes, please."
```

```
[T17] AGENT | reassuring:3 | normal | mid | normal
"There are two things going on. The charge you don't recognize is one issue. The bigger question is whether someone got into the account, because if the charge isn't yours then somebody added it — and we have to assume the account might not be safe right now."
```

```
[T18] CUSTOMER | afraid:4 | slow | mid | quiet
"Oh dear. Oh — yes, that's what I was afraid of."
```

```
[T19] AGENT | empathetic:4 | slow | mid | normal
"I know. I'm so sorry you're going through this. Your data is used solely for service provisioning and support quality, in accordance with our Privacy Policy — and the steps I'm about to take are designed to protect you while we figure out what happened."
```

```
[T20] CUSTOMER | tearful:3 | slow | mid | quiet
"Thank you. I — I'm sorry, I'm just shaken up."
```

```
[T21] AGENT | warm:3 | slow | mid | normal
"Please don't apologize. Take a breath. There's nothing you've done wrong, and we are going to get this sorted on this call. Are you okay to keep going?"
```

```
[T22] CUSTOMER | resolute:3 | slow | mid | normal
"Yes. Yes, I'm ready. Please tell me what to do."
```

```
[T23] AGENT | reassuring:3 | normal | mid | normal
"All right. Step one — I'm going to freeze the account against any further changes right now. That means no charges can be added, no payment methods can be changed, no plan adjustments — nothing. Even by me, after this freeze, until our specialist team lifts it. Doing that now."
```

```
[T24] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes, please."
```

```
[T25] AGENT | professional:3 | normal | mid | normal | (typing)
"Freeze applied."
```

```
[T26] CUSTOMER | relieved:3 | normal | mid | normal
"Oh, that's a relief."
```

```
[T27] AGENT | reassuring:3 | normal | mid | normal
"Step two — I'm flagging the account in our system as Security Review. That tells every other agent who looks at this account that it is under active investigation. Done."
```

```
[T28] CUSTOMER | cooperative:3 | normal | mid | normal
"Good."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Step three — about that two-hundred-and-forty-dollar charge. I'm freezing that specific amount so it is not collected from your card while we investigate. And I'm opening a Fraud Investigation ticket on this call. I want to be honest with you about one thing — I am not refunding the charge yet, because policy says I cannot before the investigation is finished. But it is also not coming out of your account. Those are two different things."
```

```
[T30] CUSTOMER | thoughtful:3 | slow | mid | normal
"So I don't have to pay it right now."
```

```
[T31] AGENT | reassuring:3 | normal | mid | normal
"You do not. It is on hold."
```

```
[T32] CUSTOMER | relieved:3 | normal | mid | normal
"Thank goodness."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"I'm also opening a Data Compliance ticket — that's a different team that handles the bigger question of whether someone got into the account. They are going to look at every sign-in, every change made, and confirm what happened. They will call you at the phone number on file within seventy-two hours."
```

```
[T34] CUSTOMER | curious:3 | slow | mid | normal
"Seventy-two hours. Is that — is that quick enough?"
```

```
[T35] AGENT | reassuring:3 | normal | mid | normal
"Yes — and because the account is frozen, nothing can change in the meantime. Seventy-two hours is the upper bound. In practice you'll usually hear from them sooner."
```

```
[T36] AGENT | warm:3 | normal | mid | normal | (typing)
"I'm still here with you, Ms. Holloway — just opening that ticket on my side. Thank you for your patience."
```

```
[T37] CUSTOMER | calm:2 | normal | mid | normal
"Of course, dear."
```

```
[T38] AGENT | reassuring:3 | normal | mid | normal
"All right. Both tickets are open."
```

```
[T39] AGENT | empathetic:3 | slow | mid | normal
"Step four — and this part is on your side, not mine. I want to walk you through it carefully because it matters. Do you have a pen ready to write a couple of things down?"
```

```
[T40] CUSTOMER | cooperative:3 | slow | mid | normal | (pause)
"Yes — I have a notepad."
```

```
[T41] AGENT | warm:3 | normal | mid | normal
"Wonderful. First — please change the password on your NexaLink account. If you don't know how to log in to change it, that's okay — when Data Compliance calls you, they can walk you through it."
```

```
[T42] CUSTOMER | thoughtful:3 | slow | mid | normal
"All right. Change my password. Got it."
```

```
[T43] AGENT | warm:3 | normal | mid | normal
"Second — if the email address linked to this account is one you also use for your bank, please change that email password too. The reason is that if someone got into your email, they can request password resets on any account that uses it. So we lock that down as well."
```

```
[T44] CUSTOMER | thoughtful:3 | slow | mid | normal
"Yes. Yes, that makes sense. Change email password."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"That's the most important one. If you reuse the same password anywhere else, please change those too. The Data Compliance team will give you specific guidance based on what they find — but those two are the safe starting point for today."
```

```
[T46] CUSTOMER | relieved:3 | normal | mid | normal
"Thank you. I — I feel so much better just having someone walk me through what to do."
```

```
[T47] AGENT | warm:3 | normal | mid | normal
"That's exactly what we're here for. You did the right thing by checking your bill and by calling us straight away. Many people don't notice for weeks."
```

```
[T48] AGENT | empathetic:3 | normal | mid | normal
"Just so you have the full picture — somebody, or possibly an internal system error, added a two-hundred-and-forty-dollar charge to your account that you did not authorize. Until our specialist team confirms what happened, your account is frozen and the charge is on hold."
```

```
[T49] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported a two-hundred-and-forty-dollar charge you don't recognize, I froze the account against all changes, I flagged it as Security Review, I opened a Fraud Investigation ticket for the disputed charge with four-hour follow-up, and I opened a Data Compliance ticket for the broader security question with seventy-two-hour follow-up. You've written down two password changes to make on your side. Does that all sound right, Ms. Holloway?"
```

```
[T50] CUSTOMER | grateful:4 | slow | mid | normal
"Yes. Yes, that's all of it. Thank you so much, Aisha — truly. I was sick with worry about this."
```

```
[T51] AGENT | warm:3 | normal | mid | normal
"You are so welcome. Is there anything else I can help you with today, Ms. Holloway?"
```

```
[T52] AGENT | warm:3 | normal | mid | normal
"Your case reference number is N-X-L dash zero-four-seven-zero-one-nine-two. After we hang up you'll receive a brief survey — if you have a moment to share your feedback, we'd really appreciate it. Take care of yourself, Ms. Holloway. We'll be in touch very soon."
```
