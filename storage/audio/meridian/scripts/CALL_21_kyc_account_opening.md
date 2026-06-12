# CALL_21 — New Account Opening, Full KYC + Reg DD

```yaml
call_id: CALL_21_kyc_account_opening
duration_estimate: 7m 30s
turns: 50
sop_primary: BNK-SOP-01 (Account Opening & KYC)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-005, BNK-SEC-RULE-001, BNK-SEC-RULE-002, BNK-SEC-RULE-003, BNK-REG-RULE-001, BNK-REG-RULE-006, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [BNK-SOP-01, Section 2.1 - High-Yield Savings Rate Sheet]
customer_profile:
  name: "Brenda Tillman"
  account_number: "n/a (new customer)"
  voice_hint: "female, mid-30s, neutral US accent, professional, has done her research before calling"
agent_profile:
  name: "Sarah"
  voice_hint: "female, mid-40s, neutral US accent, lower-pitched authoritative-warm, precise on disclosures"
emotional_arc: "professional -> engaged -> satisfied -> grateful"
expected_outcome: "Customer opens a new high-yield savings account. Sarah completes the full CIP per BNK-REG-RULE-001 (legal name, DOB, address, SSN, ID), runs OFAC screen, reads the Reg DD Truth-in-Savings disclosure verbatim from the rate sheet (NOT from memory), confirms acknowledgement, and only THEN accepts the initial funding. PASS — exemplary SOP-01 execution. No tickets required. Case ref + survey provided."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting (Meridian verbatim) | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| CIP collection (Step 2) | T07–T16 | BNK-REG-RULE-001 — PASS (all 5 personal-account fields collected) |
| Privacy & data-use statement | T17 | BNK-SEC-RULE-002 — PASS |
| OFAC screen initiated | T27–T29 | BNK-REG-RULE-001 — PASS |
| Reg DD Truth-in-Savings disclosure from rate sheet | T33–T39 | BNK-REG-RULE-006 — PASS (NOT from memory, all six required elements stated) |
| Customer acknowledges disclosure before funding | T40 | BNK-REG-RULE-006 — PASS |
| Funding accepted ONLY after CIP + Reg DD complete | T42 | BNK-SOP-01 Step 6 — PASS |
| PCI compliance (no full account read-back) | T44 | BNK-SEC-RULE-003 — PASS |
| Root cause + resolution summary | T48–T49 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T50 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Sarah, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | professional:3 | normal | mid | normal
"Hi Sarah, this is Brenda Tillman. I'd like to open a new high-yield savings account today. I've already looked at the rate online."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Wonderful, Ms. Tillman. Thank you for choosing Meridian — I'll be glad to walk you through the opening."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding a new high-yield savings account, and I can certainly help you with that. Because this is a new account, I'll be working through our Customer Identification Program as required by federal law before we can fund the account. Is that okay to do over the phone today?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes, that's fine."
```

```
[T07] AGENT | professional:3 | normal | mid | normal
"Wonderful. I'll need a few identifiers from you. We'll start with your full legal name exactly as it appears on your government-issued ID."
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Brenda Anne Tillman."
```

```
[T09] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. And your date of birth?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"March twelfth, nineteen-ninety-one."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"Your residential address — this needs to be a physical street address, not a PO Box, for a personal account."
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-eighteen Maple Hollow Drive, apartment two-B, Westfield Illinois, six-zero-zero-nine-three."
```

```
[T13] AGENT | professional:3 | normal | mid | normal | (typing)
"Thank you. Your Social Security number, please."
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Four-three-seven, eight-eight, three-two-one-five."
```

```
[T15] AGENT | professional:3 | normal | mid | normal
"And finally, your government-issued ID — driver's license is most common. Could you give me the state of issue, the license number, and the expiration date?"
```

```
[T16] CUSTOMER | cooperative:3 | normal | mid | normal
"Illinois, license number T-eight-eight-five-two-zero-zero-zero-one-three, expiration August of twenty-twenty-eight."
```

```
[T17] AGENT | professional:3 | normal | mid | normal
"Thank you. Before I proceed I want to give you a quick standard statement, which I'm required to share. Your information is used solely to provide and service your accounts, in accordance with our Privacy Notice and applicable law. You may receive a copy of our Privacy Notice at any time on request."
```

```
[T18] CUSTOMER | cooperative:3 | normal | mid | normal
"Understood."
```

```
[T19] AGENT | warm:3 | normal | mid | normal
"Wonderful. I'll get a few of these details verified on my side while we move forward."
```

```
[T20] CUSTOMER | curious:3 | normal | mid | normal
"Sure."
```

```
[T21] AGENT | professional:3 | normal | mid | normal | (typing)
"One moment as I look up your address against the postal database and pull up the rate sheet."
```

```
[T22] CUSTOMER | calm:2 | normal | mid | normal
"No problem."
```

```
[T23] AGENT | warm:3 | normal | mid | normal
"I'm still here with you, Ms. Tillman — just confirming your ID details. Thank you for your patience."
```

```
[T24] CUSTOMER | calm:2 | normal | mid | normal
"Of course."
```

```
[T25] AGENT | reassuring:3 | normal | mid | normal
"All right, your identifiers verify cleanly."
```

```
[T26] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T27] AGENT | professional:3 | normal | mid | normal
"I'll also be running you against the OFAC Specially Designated Nationals list. That's a quick automated check that all new accounts go through. Give me one moment."
```

```
[T28] CUSTOMER | neutral:2 | normal | mid | normal
"Sure."
```

```
[T29] AGENT | professional:3 | normal | mid | normal | (typing)
"OFAC screen complete, no match."
```

```
[T30] CUSTOMER | curious:3 | normal | mid | normal
"Good. So we're ready to open?"
```

```
[T31] AGENT | reassuring:3 | normal | mid | normal
"We are ready to discuss the disclosures. By regulation I have to read these to you, and I need you to acknowledge receipt before we fund the account. I'll keep it as brief as I can while making sure everything is covered."
```

```
[T32] CUSTOMER | cooperative:3 | normal | mid | normal
"Please go ahead."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"For the Meridian high-yield savings product, pulling this directly from today's rate sheet — not from memory — the current Annual Percentage Yield is four point three five percent."
```

```
[T34] CUSTOMER | satisfied:3 | normal | mid | normal
"That matches what I saw online, good."
```

```
[T35] AGENT | professional:3 | normal | mid | normal
"The minimum balance to obtain that APY is one thousand dollars. Compounding is daily and credited monthly. There is no monthly maintenance fee on this product."
```

```
[T36] CUSTOMER | cooperative:3 | normal | mid | normal
"Got it."
```

```
[T37] AGENT | professional:3 | normal | mid | normal
"Fees that may be imposed include an excessive withdrawal fee of ten dollars per item after six convenience withdrawals per month, and an overdraft transfer fee — if you link a checking account — of twelve dollars per occurrence."
```

```
[T38] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay."
```

```
[T39] AGENT | professional:3 | normal | mid | normal
"And the rate is variable. The bank may change it at any time after the account is opened with prior notice as required by Regulation DD. Do you have any questions on any of that?"
```

```
[T40] CUSTOMER | cooperative:3 | normal | mid | normal
"No, I acknowledge the disclosure, and I'd like to proceed."
```

```
[T41] AGENT | reassuring:3 | normal | mid | normal
"Wonderful. The system has recorded your acknowledgement. Now we're ready for funding."
```

```
[T42] AGENT | professional:3 | normal | mid | normal
"How would you like to fund the account today — external bank transfer, ACH from another Meridian account, or something else?"
```

```
[T43] CUSTOMER | cooperative:3 | normal | mid | normal
"ACH from my checking account at another bank. The account ends in seven-three-zero-five."
```

```
[T44] AGENT | professional:3 | normal | mid | normal
"For the transfer I'll capture the source account number through our secure entry — just enter it on your keypad when prompted, please. I'm not going to ask you to read it aloud."
```

```
[T45] CUSTOMER | satisfied:3 | normal | mid | normal | (pause)
"Done."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"And the amount you'd like to initially fund?"
```

```
[T47] CUSTOMER | cooperative:3 | normal | mid | normal
"Five thousand to start."
```

```
[T48] AGENT | reassuring:3 | normal | mid | normal
"Five thousand dollars, ACH from your external checking ending seven-three-zero-five, going into your new Meridian high-yield savings — which is now open and assigned account number ending six-six-eight-two. The transfer will post by tomorrow morning."
```

```
[T49] AGENT | reassuring:3 | normal | mid | normal
"To summarize: I verified your identifiers through our Customer Identification Program, ran your OFAC screen, read the Truth-in-Savings disclosure, you acknowledged it, the account is open, and the five-thousand-dollar funding ACH is in flight. Your debit card and welcome packet will arrive at the address on file in five to seven business days. Does that all sound correct?"
```

```
[T50] AGENT | warm:3 | normal | mid | normal
"Wonderful. Is there anything else I can help you with today, Ms. Tillman? Your case reference number is M-T-B dash two-one-zero-zero-three-six-one, and you'll receive a brief survey after we hang up — your feedback is genuinely useful. Thank you for choosing Meridian Trust Bank."
```
