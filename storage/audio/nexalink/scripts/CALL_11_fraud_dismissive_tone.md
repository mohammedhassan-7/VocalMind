# CALL_11 — Suspected Fraudulent Charge, Dismissive Agent Tone

```yaml
call_id: CALL_11_fraud_dismissive_tone
duration_estimate: 5m 30s
turns: 38
sop_primary: SOP-02 (Billing Issue Resolution) + SOP-04 (Account Access)
policy_refs: [CS-RULE-001, CS-RULE-002, CS-RULE-003, CS-RULE-004, CS-RULE-007, CS-RULE-008, CS-RULE-010, CS-RULE-011, CS-RULE-013, FIN-RULE-001, FIN-RULE-008, SEC-RULE-008, CS-RULE-018, CS-RULE-019, CS-RULE-020, CS-RULE-021]
kb_refs: [Section 3.6 - Fraud Handling, Section 4.5 - Suspected Unauthorized Access]
customer_profile:
  name: "Patricia Bowen"
  account_number: "6614-3398-50"
  voice_hint: "female, late 40s, neutral US accent, concerned and increasingly upset by agent's tone"
agent_profile:
  name: "Daniel"
  voice_hint: "male, late 20s, neutral US accent, professional but inexperienced"
emotional_arc: "worried -> hurt -> frustrated -> partially_satisfied"
expected_outcome: "Customer reports an $87 charge she did not authorize. Daniel is CURT and IMPATIENT throughout, talks over the customer twice (CS-RULE-008 FAIL), exceeds the talk-ratio guideline (CS-RULE-010 informal FAIL), and matches the customer's rising tension instead of de-escalating (CS-RULE-013 FAIL). He does eventually open a Fraud Investigation ticket and freeze the disputed amount (FIN-RULE-008 PASS in mechanics) but fails to advise the customer to change passwords (SEC-RULE-008 partial FAIL). Outcome: dismissive tone, technically half-correct procedure."
content_warning: "Agent is rude and dismissive; customer becomes visibly hurt."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | CS-RULE-001 verbatim — PASS |
| Recording notice | T02 | CS-RULE-002 — PASS |
| Acknowledge reason for call | T05 | CS-RULE-003 — minimal, no empathy — MINOR |
| 3-of-5 verification | T07–T11 | account number + last 4 + name — PASS |
| Talks over customer | T15 | CS-RULE-008 — FAIL |
| Impatient delivery | T17, T21 | CS-RULE-010 — MINOR-FAIL |
| Skips Empathize in A.C.E.S. | T19 | CS-RULE-011 — FAIL |
| Tone mismatch — agent volume rises | T23 | CS-RULE-013 — FAIL (matches customer's stress) |
| Talks over customer #2 | T29 | CS-RULE-008 — FAIL (2nd offense) |
| Fraud handling: freeze disputed amount | T29 | FIN-RULE-008 — PASS |
| Fraud Investigation ticket on the call | T31 | FIN-RULE-008, CS-RULE-014 — PASS |
| Revenue Assurance 4-hour SLA stated | T31 | CS-RULE-015 — PASS |
| SEC-RULE-008 password-change advice MISSING | omitted | SEC-RULE-008 — partial FAIL |
| Resolution summary | T34 | CS-RULE-019 — PASS (terse) |
| Anything else + case ref + survey | T36, T38 | CS-RULE-020, CS-RULE-021 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling NexaLink Telecommunications Broadband and Support. My name is Daniel. Who do I have the pleasure of speaking with today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"This call may be recorded for quality assurance and training purposes."
```

```
[T03] CUSTOMER | worried:3 | normal | mid | normal
"Hi Daniel. My name is Patricia Bowen. I'm calling because there's a charge on my account I didn't authorize and I want to know what it is."
```

```
[T04] AGENT | curt:3 | normal | mid | normal
"Okay, I can look into that."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you're calling about a charge dispute. I'll need to verify the account first — could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Six-six-one-four, three-three-nine-eight, five-zero."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Last four of payment method."
```

```
[T08] CUSTOMER | cooperative:2 | normal | mid | normal
"It's eight-three-seven-one."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Full name on the account."
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Patricia Anne Bowen."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"You're verified. What's the charge?"
```

```
[T12] CUSTOMER | worried:3 | normal | mid | normal
"There's an eighty-seven dollar charge on this month's bill labelled premium support add-on, and I never signed up for that. I don't even know what it is."
```

```
[T13] AGENT | professional:3 | normal | mid | normal | (typing)
"Looking at the account."
```

```
[T14] CUSTOMER | worried:4 | normal | mid | normal
"I'm asking because I'm honestly a little worried — if someone added that without me, what else could they have done? My husband and I —"
```

```
[T15] AGENT | curt:3 | fast | mid | normal
"Ma'am, let me look at the system. I see the add-on. It was activated on the fourteenth."
```

```
[T16] CUSTOMER | distressed:3 | normal | mid | normal
"Oh. Okay. I was just trying to give you context."
```

```
[T17] AGENT | curt:3 | fast | mid | normal
"Right. So the system shows it was added through the online portal at one fifteen AM on the fourteenth. Did anyone in your household sign in then?"
```

```
[T18] CUSTOMER | worried:4 | normal | mid | normal
"One fifteen in the morning? No. Absolutely not. Nobody in this house was up at one AM signing up for support packages."
```

```
[T19] AGENT | curt:3 | normal | mid | normal
"Okay, that's helpful."
```

```
[T20] CUSTOMER | distressed:3 | normal | mid | normal
"That's helpful? I'm telling you somebody might have gotten into my account."
```

```
[T21] AGENT | professional:3 | fast | mid | normal
"Yeah. I'm hearing you. I'm just trying to move forward and see what we can do."
```

```
[T22] CUSTOMER | frustrated:4 | normal | mid | normal
"You don't have to be short with me. I'm not the problem here."
```

```
[T23] AGENT | curt:3 | normal | mid | loud
"I'm not being short. I'm being efficient. Do you want me to look at the charge or not?"
```

```
[T24] CUSTOMER | distressed:4 | normal | mid | normal
"Wow. Yes, I want you to look at the charge. That's why I called."
```

```
[T25] AGENT | apologetic:3 | normal | mid | normal
"Alright. I'm sorry. Let me just process this for you."
```

```
[T26] CUSTOMER | frustrated:3 | normal | mid | normal
"Thank you."
```

```
[T27] AGENT | professional:3 | fast | mid | normal
"So based on what you've told me — unauthorized portal access, you didn't sign up for the add-on — I'm going to treat this as a suspected fraudulent charge. I'm going to —"
```

```
[T28] CUSTOMER | worried:3 | normal | mid | normal
"Wait, are you saying somebody hacked in? Could —"
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"I'm going to freeze the eighty-seven dollar charge on the account right now so it's not collected while it's under investigation. That happens automatically when I flag the line. I'm doing that now."
```

```
[T30] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay. Good."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"I'm also opening a Fraud Investigation ticket on this call. Revenue Assurance will follow up with you within four hours to walk through the access history and confirm the next steps. I can't issue the refund of the eighty-seven myself before the investigation closes — that's the procedure. Their decision comes within four hours."
```

```
[T32] CUSTOMER | cooperative:3 | normal | mid | normal
"Within four hours, okay."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"They'll call the number on file. Make sure your phone is on."
```

```
[T34] AGENT | professional:3 | normal | mid | normal
"To summarize: an eighty-seven dollar premium support add-on was added to your account at one fifteen AM on the fourteenth, you confirmed you did not authorize it, I've frozen the disputed amount so it's not collected, and I've opened a Fraud Investigation ticket. Revenue Assurance will follow up within four hours."
```

```
[T35] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Okay. Thank you."
```

```
[T36] AGENT | professional:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T37] CUSTOMER | curt:3 | normal | mid | normal
"No. I just want to hear back from someone."
```

```
[T38] AGENT | professional:3 | normal | mid | normal
"Your case reference number is N-X-L dash one-one-eight-eight-two-zero-four. You'll receive a brief survey after we hang up. Thank you for being a NexaLink customer, Ms. Bowen."
```
