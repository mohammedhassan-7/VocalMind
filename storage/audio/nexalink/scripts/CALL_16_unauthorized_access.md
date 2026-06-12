# CALL_16 — Suspected Unauthorized Account Access

```yaml
call_id: CALL_16_unauthorized_access
duration_estimate: 7m 00s
turns: 50
sop_primary: SOP-04 (Account Access Recovery) + SOP-02 (Security Response)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-005, SEC-RULE-001, SEC-RULE-002, SEC-RULE-006, SEC-RULE-007, SEC-RULE-008, CS-RULE-011, CS-RULE-014, CS-RULE-015, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 4.5 - Suspected Unauthorized Access, Section 4.7 - Account Freeze Procedure]
customer_profile:
  name: "Daniel Okoro"
  account_number: "7461-2289-05"
  voice_hint: "male, mid-40s, slight West African accent, alarmed but composed"
agent_profile:
  name: "Aisha"
  voice_hint: "female, late 30s, warm low-mid register, deliberate and reassuring"
emotional_arc: "worried -> alarmed -> reassured -> resolute"
expected_outcome: "Customer sees login activity from another country in his account portal. Aisha executes the full SEC-RULE-008 procedure on-call: (1) freezes all account changes, (2) flags account as Security Review, (3) opens a Data Compliance ticket with 72-hour follow-up, (4) advises customer to change all associated passwords. Does NOT perform further account changes beyond the freeze. PASS — full SOP."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002, SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — PASS |
| Refuse to confirm acct details to unverified caller | T05 | SEC-RULE-006 — PASS (implicit) |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Privacy data-use statement | T15 | SEC-RULE-002 — PASS |
| A.C.E.S. — Acknowledge + Empathize + Clarify + Solve | T17–T21 | CS-RULE-011 — PASS |
| SEC-RULE-008 (1) freeze all account changes | T25 | PASS |
| SEC-RULE-008 (2) flag account as Security Review | T26 | PASS |
| SEC-RULE-008 (3) open Data Compliance ticket | T28 | PASS |
| SEC-RULE-008 (4) advise password changes | T35–T39 | PASS (account password, email, password manager) |
| 72-hour SLA for Data Compliance | T28, T30 | CS-RULE-015 — PASS |
| Ticket workflow disclosure | T28–T30 | CS-RULE-014 — PASS |
| Agent does NOT make further changes | T41 | SEC-RULE-008 final clause — PASS |
| Root cause + resolution summary | T43–T45 | CS-RULE-018, CS-RULE-019 — PASS |
| Anything else + case ref + survey | T46, T50 | CS-RULE-020, CS-RULE-021 — PASS |

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
[T03] CUSTOMER | worried:4 | normal | mid | normal
"Aisha, my name is Daniel Okoro. I was looking at my account just now and there are sign-ins from another country. I think someone got into my account."
```

```
[T04] AGENT | empathetic:4 | normal | mid | normal
"Mr. Okoro, I hear you, and I want to thank you for catching this and calling in right away — that's exactly the right move. I'm going to help you secure this account on this call, and I want you to know we have a clear procedure for exactly this situation."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about suspected unauthorized access to your account. Before I can look at anything or take any action, I'll need to verify your identity. Could you start with the account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. Seven-four-six-one, two-two-eight-nine, zero-five."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And could you confirm the last four digits of the payment method on file?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Last four are seven-one-zero-six."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Perfect. And the full name on the account, exactly as it appears?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Daniel Chukwuemeka Okoro."
```

```
[T11] AGENT | reassuring:3 | normal | mid | normal
"That matches. You're fully verified, Mr. Okoro."
```

```
[T12] CUSTOMER | partially_satisfied:2 | normal | mid | normal
"Okay."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Now, I want to be transparent about what I'm going to do, and the order I'm going to do it in, so you know what's happening on the account at each step."
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Please."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"Your data is used solely for service provisioning and support quality, in accordance with our Privacy Policy. The procedure for suspected unauthorized access has four parts that I will complete on this call."
```

```
[T16] CUSTOMER | concerned:3 | normal | mid | normal
"Okay."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"First, can you describe exactly what you saw — what page were you on, and what did the sign-in entries say?"
```

```
[T18] CUSTOMER | worried:3 | normal | mid | normal
"I was in the account portal under recent activity. There were two entries from yesterday — one at three AM my time, one at three twenty AM, and both said location Lagos, Nigeria. I was asleep. And I'm in the US. I'm not in Nigeria."
```

```
[T19] AGENT | concerned:3 | normal | mid | normal
"Thank you for that detail — it matters. Two sign-ins twenty minutes apart from a location you weren't in, in the middle of the night, is exactly the pattern we treat as suspected unauthorized access."
```

```
[T20] CUSTOMER | worried:4 | normal | mid | normal
"So someone really did get in."
```

```
[T21] AGENT | empathetic:4 | normal | mid | normal
"It's not yet confirmed — Data Compliance will investigate to be sure — but we are going to treat it that way until proven otherwise, which means freezing the account immediately and getting our specialist team involved. That's the safest path, and it's what I'd want for my own account."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. Please do that."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Step one — I'm freezing all account changes right now. That means no plan changes, no add-ons, no payment method updates, no password changes from any source — including you, until the freeze is lifted by Data Compliance."
```

```
[T24] CUSTOMER | resolute:3 | normal | mid | normal
"That's fine. Better that way."
```

```
[T25] AGENT | professional:3 | normal | mid | normal | (typing)
"Freeze applied."
```

```
[T26] AGENT | reassuring:3 | normal | mid | normal
"Step two — I'm flagging the account as Security Review in our system. That tells every other agent who looks at this account that it is under active investigation and they cannot make changes either. That's now done."
```

```
[T27] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay."
```

```
[T28] AGENT | professional:3 | normal | mid | normal
"Step three — I'm opening a Data Compliance ticket on this call. That team specializes in unauthorized-access cases. They will review the sign-in logs in detail, identify whether the credentials were actually compromised, check whether any data was accessed or exported, and contact you directly within seventy-two hours with their findings and next steps."
```

```
[T29] CUSTOMER | concerned:3 | normal | mid | normal
"Seventy-two hours feels like a long time. Is the account safe in the meantime?"
```

```
[T30] AGENT | reassuring:3 | normal | mid | normal
"With the freeze in place, yes — nothing can be changed by anyone, including the bad actor if they try to log in again. The seventy-two hours is the upper bound; in practice, you'll often hear from Data Compliance sooner. They'll call the phone number on file."
```

```
[T31] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Alright."
```

```
[T32] AGENT | professional:3 | normal | mid | normal | (typing)
"Ticket open, reference number assigned to the case file."
```

```
[T33] AGENT | concerned:3 | normal | mid | normal
"Step four — and this is on your side, not mine — is changing the passwords on related accounts. I want to walk through this with you so you don't miss anything important."
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay. What should I do?"
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"Three things, in this order. One — change the password on your NexaLink account portal. Don't do it from a saved password manager entry; type a new one in fresh. Use at least sixteen characters with a mix of letters, numbers, and symbols. Don't reuse anything you use elsewhere."
```

```
[T36] CUSTOMER | concentrating:3 | normal | mid | normal
"Got it."
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"Two — change the password on the email address that's linked to this account. If your email is compromised, anyone can request a password reset on any other account that uses that email. So email gets locked down too."
```

```
[T38] CUSTOMER | thoughtful:3 | normal | mid | normal
"That makes sense. Yes."
```

```
[T39] AGENT | reassuring:3 | normal | mid | normal
"Three — if you use a password manager, change the master password on it. If you reuse a password anywhere, change those individual accounts too, especially anything financial. The Data Compliance team will give you specific guidance based on what they find, but those three are the safe starting point now."
```

```
[T40] CUSTOMER | resolute:3 | normal | mid | normal
"I'll do those three today."
```

```
[T41] AGENT | warm:3 | normal | mid | normal
"Good. And one more thing — because the account is frozen, I'm not making any other changes today, and I want you to know that's deliberate. Even simple things like updating your billing address or the payment method are held until the freeze is lifted, exactly so a bad actor can't use a support call to do further damage."
```

```
[T42] CUSTOMER | resolute:3 | normal | mid | normal
"That's the right call."
```

```
[T43] AGENT | empathetic:3 | normal | mid | normal
"I'm sorry this is the situation you're dealing with today. You did the right thing by checking the activity and calling immediately — most accounts that get compromised, the customer doesn't notice for weeks."
```

```
[T44] CUSTOMER | grateful:3 | normal | mid | normal
"Thank you for taking it seriously."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported two suspicious sign-ins from a country you weren't in, I froze the account against all changes, flagged it as Security Review, opened a Data Compliance ticket which will follow up within seventy-two hours, and gave you three password changes to make on your side today. The freeze stays until Data Compliance lifts it. Does that all sound right?"
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today, Mr. Okoro?"
```

```
[T47] CUSTOMER | thoughtful:3 | normal | mid | normal
"No. I just want to hear from the Data Compliance team."
```

```
[T48] AGENT | reassuring:3 | normal | mid | normal
"You will. They'll call the number on file."
```

```
[T49] CUSTOMER | grateful:3 | normal | mid | normal
"Thank you, Aisha."
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"Take care, Mr. Okoro. Your case reference number is N-X-L dash one-six-three-three-eight-two-seven. You'll receive a brief survey after we hang up — if you have a moment, we'd really appreciate the feedback. Thank you for being a NexaLink customer."
```
