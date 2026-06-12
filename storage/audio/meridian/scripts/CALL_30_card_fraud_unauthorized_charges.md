# CALL_30 — Card Fraud, Multiple Unauthorized Charges

```yaml
call_id: CALL_30_card_fraud_unauthorized_charges
duration_estimate: 7m 15s
turns: 50
sop_primary: BNK-SOP-02 (Reg E Dispute Resolution) + BNK-SOP-03 (Card Fraud)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-REG-RULE-007, BNK-REG-RULE-008, BNK-FIN-RULE-002, BNK-FIN-RULE-004, BNK-FIN-RULE-005, BNK-FRAUD-RULE-001, BNK-FRAUD-RULE-002, BNK-FRAUD-RULE-004, BNK-FRAUD-RULE-005, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-02 Reg E, BNK-SOP-03 Card Fraud]
customer_profile:
  name: "Lillian Park"
  account_number: "M-T-B 5572-1409-83"
  voice_hint: "female, late 30s, neutral US accent, alarmed but calm under pressure"
agent_profile:
  name: "Jasmine"
  voice_hint: "female, late 30s, warm calm low-mid register, deliberate and reassuring; fraud specialist"
emotional_arc: "alarmed -> reassured -> cooperative -> relieved"
expected_outcome: "Customer reports $1,247 in unauthorized card charges from a card she still has in her possession (skimming or data-breach exposure). Jasmine closes the card, orders expedited replacement, takes the Reg E claim verbally, issues $500 provisional credit at her authority (BNK-FIN-RULE-004 PASS), opens a Manager Approval ticket for the remaining $747 since the total exceeds her cap (BNK-FIN-RULE-002 PASS — does not promise the full amount). PASS — exemplary fraud-specialist handling with correct authority limits respected."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| A.C.E.S. — full sequence | T15, T19, T23 | BNK-CC-RULE-012 — PASS |
| Card closed immediately | T25 | BNK-FRAUD-RULE-002 — PASS |
| Expedited replacement ordered (fee waived for fraud) | T27 | BNK-FRAUD-RULE-002 — PASS |
| Reg E claim verbal (no written form required first) | T31 | BNK-REG-RULE-008 — PASS |
| Provisional credit within $500 cap | T35 | BNK-FIN-RULE-004 — PASS |
| Manager Approval ticket for amount above cap (no number promised) | T35, T37 | BNK-FIN-RULE-002, BNK-FIN-RULE-005 — PASS |
| Reg E timeline verbatim | T39 | BNK-REG-RULE-007 — PASS |
| Fraud Operations ticket SLA (4-hr + 10-BD) | T41 | BNK-FRAUD-RULE-004 — PASS |
| Does NOT promise full refund before investigation | T37 | BNK-FRAUD-RULE-005 — PASS |
| Root cause + resolution summary | T45–T46 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T48, T50 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Jasmine, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | worried:4 | normal | mid | normal
"Hi Jasmine, I'm Lillian Park. I just opened my online banking and there are six charges on my debit card I didn't make. About twelve hundred dollars total. I have my card right here in my wallet."
```

```
[T04] AGENT | empathetic:4 | normal | mid | normal
"Lillian, I am so glad you called us right away — that is exactly the right move. I'm a fraud specialist, so this is in the right hands. We're going to work through this together and I'll keep you informed at every step."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling about unauthorized charges on your debit card, and I can certainly help with that. Before I look at the account I'll need to verify a few details. Could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Five-five-seven-two, one-four-zero-nine, eight-three."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. Date of birth?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"March twenty-fourth, nineteen-eighty-six."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-four-seven-two."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the full legal name on the account?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Lillian Joy Park."
```

```
[T13] AGENT | reassuring:3 | normal | mid | normal
"You're fully verified, Lillian."
```

```
[T14] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Thank you."
```

```
[T15] AGENT | empathetic:3 | normal | mid | normal
"Let me look at the charges with you. Walk me through what you're seeing — which merchants, what amounts, what dates."
```

```
[T16] CUSTOMER | concerned:3 | normal | mid | normal
"Yesterday afternoon. Six charges, all between fifty and three hundred dollars. Merchants I have never heard of — one is in Florida, two are online retailers I don't recognize, three are at a gas station chain I've never used. I'm here in Boston, I have my card in my hand, and I haven't been to Florida in years."
```

```
[T17] AGENT | concerned:3 | normal | mid | normal
"Thank you for the detail. With your card in your possession and charges happening in Florida, that pattern is classic skimming or a data-breach exposure. The criminal got your card data — number, expiration, and likely PIN if your transactions cleared at the gas pumps — and they're using a cloned card."
```

```
[T18] CUSTOMER | distressed:4 | normal | mid | normal
"Oh no. So my actual card is fine but they have my number?"
```

```
[T19] AGENT | empathetic:4 | normal | mid | normal
"That's exactly it. And the very good news here is that under Regulation E you have full consumer protection. As long as you report this within sixty days of your statement, you are protected from those unauthorized charges. We are well within that window."
```

```
[T20] CUSTOMER | relieved:3 | normal | mid | normal
"Oh, that's a relief."
```

```
[T21] AGENT | reassuring:3 | normal | mid | normal
"It is a relief. Now let me walk you through what I'm going to do. Five steps."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"Please."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"Step one — closing your card right now. The cloned version is going to keep being used until I shut it down on our side."
```

```
[T24] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes — please do that immediately."
```

```
[T25] AGENT | professional:3 | normal | mid | normal | (typing)
"Card is closed. No further charges can post against that card number, including the cloned version the criminal is using."
```

```
[T26] CUSTOMER | relieved:3 | normal | mid | normal
"Good."
```

```
[T27] AGENT | professional:3 | normal | mid | normal
"Step two — ordering a replacement card. Standard delivery is three to five business days, but because this is fraud the expedited fee is waived. I can have it on your doorstep tomorrow morning if you'd like."
```

```
[T28] CUSTOMER | cooperative:3 | normal | mid | normal
"Tomorrow morning. Yes, please."
```

```
[T29] AGENT | professional:3 | normal | mid | normal | (typing)
"Expedited replacement ordered to the address on file. Confirmation will email to you within the hour."
```

```
[T30] CUSTOMER | satisfied:3 | normal | mid | normal
"Wonderful."
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"Step three — opening the Regulation E dispute. I'm going to take this as a verbal claim, which is your right under Reg E. You don't need to sign a written form before I issue provisional credit. The written claim will follow within ten business days — we'll mail it to you and you sign and return."
```

```
[T32] CUSTOMER | cooperative:3 | normal | mid | normal
"Got it."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"Step four — the provisional credit. I want to be transparent about how this works, because the math matters here. Total disputed is twelve hundred forty-seven dollars across six charges. My single-call provisional credit authority is up to five hundred dollars."
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"So here's what I'm going to do. I'm going to issue five hundred dollars in provisional credit to your account right now under my own authority. That gives you immediate access to that money while the investigation runs. For the remaining seven hundred forty-seven dollars, I'm not going to promise you a number I can't authorize myself — instead I'm opening a Manager Approval ticket for that amount, which will be decided within one business day."
```

```
[T36] CUSTOMER | curious:3 | normal | mid | normal
"So the five hundred is mine today, and the rest comes within a day?"
```

```
[T37] AGENT | reassuring:3 | normal | mid | normal
"That's right — and for the final outcome on all twelve hundred forty-seven, that's the Reg E adjudication team's call within ten business days. Given that the pattern is obvious skimming, charges in a city you weren't in, and you have your physical card, the outcome should be clean. But the decision is theirs, not mine."
```

```
[T38] CUSTOMER | cooperative:3 | normal | mid | normal
"Understood."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"I am issuing a provisional credit of five hundred dollars today while we investigate. You will receive a written determination within ten business days. If the investigation requires additional time the timeline may extend, but the provisional credit remains in place during that period."
```

```
[T40] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Good."
```

```
[T41] AGENT | professional:3 | normal | mid | normal | (typing)
"Step five — opening the Fraud Operations ticket. They'll contact you within four hours to gather any additional details, and the final determination is within ten business days."
```

```
[T42] CUSTOMER | curious:3 | normal | mid | normal
"What additional details would they need?"
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"Things like — where you last used the card recently, in case we can spot the compromise point. Any merchant where you might have used the card with your PIN. Whether you ever respond to text messages asking you to verify card activity. Things like that. They'll guide you."
```

```
[T44] CUSTOMER | thoughtful:3 | normal | mid | normal
"Got it. I'll be ready when they call."
```

```
[T45] AGENT | empathetic:3 | normal | mid | normal
"And just so you have the full picture — what happened here is what we call card-present-elsewhere fraud. Your physical card never left you, but somewhere recently your card data was captured — either at a compromised gas pump, a tampered ATM, a hacked online merchant, or a third-party data breach. The criminal then loaded that data onto a cloned card and used it where they're located. Closing the old card and issuing a new one with a fresh number breaks that loop entirely."
```

```
[T46] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported six unauthorized charges totaling twelve hundred forty-seven dollars on your debit card while it was in your possession. I closed the compromised card, ordered an expedited replacement for tomorrow morning, opened a verbal Reg E claim, issued five hundred dollars in provisional credit today within my authority, opened a Manager Approval ticket for the remaining seven hundred forty-seven dollars with a one-business-day decision, and opened a Fraud Operations ticket with a four-hour follow-up and ten-business-day final determination. Does that all sound right, Lillian?"
```

```
[T47] CUSTOMER | grateful:3 | normal | mid | normal
"Yes. Honestly, I was sick when I saw the charges this morning. You handled this so well — I feel like it's actually going to be okay."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"That is exactly the outcome I wanted. Is there anything else I can help you with today, Lillian?"
```

```
[T49] CUSTOMER | satisfied:3 | normal | mid | normal
"No, that's all of it. Thank you so much, Jasmine."
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is M-T-B dash three-zero-zero-five-one-one-four. You'll receive a brief survey after we hang up — your feedback is genuinely useful. Take care, Lillian."
```
