# CALL_29 — Business Check Fraud (Forged Checks)

```yaml
call_id: CALL_29_check_fraud_business
duration_estimate: 7m 00s
turns: 50
sop_primary: BNK-SOP-03 (Fraud Investigation, Check Fraud)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-007, BNK-CC-RULE-008, BNK-CC-RULE-010, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-FRAUD-RULE-001, BNK-FRAUD-RULE-003, BNK-FRAUD-RULE-004, BNK-FRAUD-RULE-005, BNK-FRAUD-RULE-009, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-03 Fraud Investigation - Check Fraud, Affidavit of Forgery]
customer_profile:
  name: "Theo Marchetti"
  account_number: "M-T-B-BIZ 6629-8814-22"
  voice_hint: "male, mid-50s, neutral US accent with a faint New Jersey edge, owns a small construction firm, alarmed but composed"
agent_profile:
  name: "Andre"
  voice_hint: "male, mid-30s, neutral US accent, friendly methodical cadence"
emotional_arc: "alarmed -> validated -> cooperative -> reassured"
expected_outcome: "Business customer discovers three forged checks totalling $4,820 cleared his account this week. Andre completes Enhanced Verification (business control person + 5-of-5), places check-by-check holds, images the disputed items, opens a Fraud Operations ticket, schedules the Affidavit of Forgery for the customer to complete. Does NOT promise a refund before investigation (BNK-FRAUD-RULE-005 PASS). One minor BNK-CC-RULE-008 dead-air slip while pulling check images. PASS overall with minor coachable moment."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| Enhanced Verification (5-of-5 for high-risk) | T07–T15 | BNK-CC-RULE-007 — PASS |
| A.C.E.S. — Acknowledge + Empathize | T19, T23 | BNK-CC-RULE-012 — PASS |
| MINOR slip: silence while pulling images | T29–T30 | BNK-CC-RULE-008 — MINOR FAIL (dead air > 5s before re-engage) |
| Re-engagement during silent task | T31 | BNK-CC-RULE-010 — PASS (after the slip) |
| BNK-FRAUD-RULE-003 image disputed items | T29 | PASS |
| BNK-FRAUD-RULE-001 freeze applied (check-by-check hold) | T33 | PASS |
| Fraud Operations ticket opened | T35 | BNK-CC-RULE-015 — PASS |
| BNK-FRAUD-RULE-004 SLA (4-hr follow-up, 10-BD determination) | T37 | PASS |
| **Does NOT promise refund before investigation** | T23 | BNK-FRAUD-RULE-005 — PASS (key compliance anchor) |
| Affidavit mailed to address on file (NOT to provided address) | T39, T41 | BNK-FRAUD-RULE-009 — PASS |
| Old check series voided / new ordered | T45 | Preventive — PASS |
| Root cause + resolution summary | T46–T47 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T48, T50 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Andre, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | worried:4 | normal | mid | normal
"Andre — Theo Marchetti, Marchetti Construction. I'm looking at my business account online and there are three checks cleared this week I did not write. Together it's almost five thousand dollars."
```

```
[T04] AGENT | concerned:3 | normal | mid | normal
"Mr. Marchetti, thank you for calling us right away on this. That's exactly the right move. Let me get you safely verified and we'll start protecting the account."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling about suspected forged checks on your business account. I can certainly help. Because this is fraud, I'm going to take you through Enhanced Verification, which is a few more identifiers than usual."
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Whatever you need. Go."
```

```
[T07] AGENT | professional:3 | normal | mid | normal
"Business account number?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Six-six-two-nine, eight-eight-one-four, two-two."
```

```
[T09] AGENT | professional:3 | normal | mid | normal | (typing)
"Full legal business name?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Marchetti Construction Incorporated."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"Your full legal name?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Theodore Joseph Marchetti."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Date of birth, last four of your Social, and the security challenge phrase, please?"
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"May twenty-fifth nineteen-sixty-eight. Last four, six-six-two-nine. The phrase is the name of my first dog. Bruno."
```

```
[T15] AGENT | reassuring:3 | normal | mid | normal
"All five identifiers match. Enhanced Verification complete. I have you confirmed as the control person and primary signer."
```

```
[T16] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Thank you."
```

```
[T17] AGENT | empathetic:3 | normal | mid | normal
"Walk me through what you're seeing. What do the three checks look like in the activity?"
```

```
[T18] CUSTOMER | worried:3 | normal | mid | normal
"Three checks in the seventeen hundred range. Check numbers I don't recognize. Two of them cleared Tuesday, one on Wednesday. Payable to entities I have never heard of."
```

```
[T19] AGENT | concerned:3 | normal | mid | normal
"That sounds like a counterfeit-check fraud — the criminal either lifted your routing and account number from a real check you wrote and printed their own checks, or they got it through stolen mail or a compromised payment processor. Unfortunately it's a growing pattern. The procedure for handling this is clear and you're in the right place."
```

```
[T20] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay. What do we do?"
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Four things, in this order. First, I'm going to freeze the three disputed amounts so they can't be further collected against your account. Second, I'm going to image the three checks for the Fraud Investigations team. Third, I'm opening a Fraud Operations ticket on this call. Fourth, you'll need to complete an Affidavit of Forgery, which we will mail to the address on file for the business."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. All of those. Go ahead."
```

```
[T23] AGENT | empathetic:3 | normal | mid | normal
"And before I touch anything, I want to be straight with you on one piece. I am not going to promise you a refund of the disputed amount today. The process gives us up to ten business days for the determination, and what I can do today is freeze the amounts and open the case. The refund — if approved — comes after the investigation. I know that's not the answer you were hoping for, but it's the honest one."
```

```
[T24] CUSTOMER | resolute:3 | normal | mid | normal
"I'd rather hear it straight. Keep going."
```

```
[T25] AGENT | reassuring:3 | normal | mid | normal
"That's the right attitude. Let me execute the four steps."
```

```
[T26] AGENT | professional:3 | normal | mid | normal | (typing)
"Step one — pulling up the three checks to confirm the amounts and dates."
```

```
[T27] CUSTOMER | neutral:2 | normal | mid | normal
"Okay."
```

```
[T28] AGENT | professional:3 | normal | mid | normal
"Check sixteen-zero-five, eighteen-twenty-two dollars, cleared Tuesday morning. Check sixteen-zero-six, sixteen-eighty-nine dollars, cleared Tuesday afternoon. Check sixteen-zero-seven, thirteen-zero-nine dollars, cleared Wednesday morning. Total disputed four thousand eight hundred and twenty dollars."
```

```
[T29] AGENT | professional:3 | normal | mid | normal | (typing)
"Pulling the front-and-back images on each one."
```

```
[T30] CUSTOMER | neutral:2 | normal | mid | normal
"…"
```

```
[T31] AGENT | warm:3 | normal | mid | normal
"Sorry — I should have spoken sooner. The image system is being slow today. I'm still here with you, Mr. Marchetti — pulling the third image now. Won't be much longer."
```

```
[T32] CUSTOMER | calm:2 | normal | mid | normal
"No worries."
```

```
[T33] AGENT | professional:3 | normal | mid | normal | (typing)
"All three images captured. Step one — applying the check-by-check freeze. Each of those three amounts is now flagged as disputed and the funds cannot be further collected pending investigation."
```

```
[T34] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Good."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"Step two — Fraud Operations ticket. Opening now with all three check images, the dates, the amounts, and the payee information as it appears on each check. Fraud Operations will follow up within four hours."
```

```
[T36] CUSTOMER | curious:3 | normal | mid | normal
"What does follow-up mean? They call me?"
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"Within four hours from now, Fraud Ops will call the number on file to acknowledge the ticket and gather any additional information they need. The final determination — whether the items are confirmed forged and the credit is permanent — happens within ten business days."
```

```
[T38] CUSTOMER | thoughtful:3 | normal | mid | normal
"Got it. Four hours initial, ten business days final."
```

```
[T39] AGENT | reassuring:3 | normal | mid | normal
"Exactly. Step three — the Affidavit of Forgery. This is a sworn statement that says these checks were not signed or authorized by you. It needs to be notarized — you can do that at any of our branches at no cost. We will mail the affidavit to your address on file for the business — NOT to any other address."
```

```
[T40] CUSTOMER | cooperative:3 | normal | mid | normal
"Yeah, that's the right one. The Patterson Avenue address."
```

```
[T41] AGENT | professional:3 | normal | mid | normal
"Confirmed Patterson Avenue address — and that's the only address we'll mail to. The affidavit goes out in tomorrow's mail. You should have it by Thursday."
```

```
[T42] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T43] AGENT | empathetic:3 | normal | mid | normal
"In the meantime — and this is important — please switch to electronic payments where you can, and consider closing this check series. We can issue you a new check series with different numbers so that any future checks the criminal tries to pass with your old number get rejected on sight. That can be done either now over the phone or at a branch."
```

```
[T44] AGENT | professional:3 | normal | mid | normal
"Would you like to close the old series now?"
```

```
[T45] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. New check series."
```

```
[T46] AGENT | professional:3 | normal | mid | normal | (typing)
"Done. Old series voided in the system. New check book ordered, ships in five to seven business days. Until they arrive, you can use online bill pay and ACH from the account without restriction."
```

```
[T47] AGENT | reassuring:3 | normal | mid | normal
"To give you the picture — someone got your routing and account number, almost certainly from a real check you wrote that got into the wrong hands somewhere along the line. They counterfeited checks using that account information, wrote them to themselves or to a money-mule entity, and tried to clear them before you noticed. Closing the old check series stops that path entirely going forward."
```

```
[T48] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported three forged checks totalling four thousand eight hundred and twenty dollars cleared this week. I completed Enhanced Verification, imaged all three checks, applied a check-by-check freeze on each amount, opened a Fraud Operations ticket with four-hour initial follow-up and ten-business-day determination, the Affidavit of Forgery is being mailed to your Patterson Avenue address on file, and we closed the old check series with a new one on order. Does that all sound right, Mr. Marchetti?"
```

```
[T49] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"Your case reference number is M-T-B dash two-nine-three-zero-zero-six-eight. You'll receive a brief survey after we hang up — your feedback is genuinely useful. Take care, Mr. Marchetti."
```
