# CALL_34 — Overdraft Fee Waiver Within Banker Authority

```yaml
call_id: CALL_34_overdraft_fee_waiver
duration_estimate: 6m 30s
turns: 46
sop_primary: BNK-SOP-04-adj (Fee Waiver within Authority)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-012, BNK-SEC-RULE-001, BNK-FIN-RULE-001, BNK-FIN-RULE-003, BNK-FIN-RULE-006, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [Overdraft Fee Waiver Matrix]
customer_profile:
  name: "Naomi Bridges"
  account_number: "M-T-B 5503-1148-72"
  voice_hint: "female, early 30s, neutral US accent, embarrassed about the overdraft but composed"
agent_profile:
  name: "Karen"
  voice_hint: "female, mid-30s, composed low-mid register, steady and reassuring"
emotional_arc: "apologetic -> heard -> reassured -> grateful"
expected_outcome: "Customer disputes two overdraft fees totalling $140 from a vacation week when she misjudged a debit card transaction. Within Karen's $250 cap. Karen completes BNK-FIN-RULE-003 180-day check (none in window — qualifies for first-occurrence treatment), waives both fees on the call, AND sets up overdraft transfer protection going forward. PASS — clean fee-waiver-within-authority execution."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification | T07–T13 | BNK-CC-RULE-004 — PASS |
| A.C.E.S. — full sequence | T15–T23 | BNK-CC-RULE-012 — PASS |
| BNK-FIN-RULE-003 180-day check before applying | T27 | PASS (none in window — qualifies) |
| Repeat-complaint pattern check (BNK-FIN-RULE-006) | T29 | PASS (not flagged) |
| Fee waiver within $250 cap | T31 | BNK-FIN-RULE-001 — PASS |
| Overdraft transfer protection set up going forward | T37–T40 | Preventive — PASS |
| Root cause + resolution summary | T42–T43 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T44, T46 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

---

## Dialog

```
[T01] AGENT | professional:3 | normal | mid | normal
"Thank you for calling Meridian Trust Bank. My name is Karen, how may I help you today?"
```

```
[T02] AGENT | professional:3 | normal | mid | normal
"Please note this call is recorded for quality assurance and regulatory compliance purposes."
```

```
[T03] CUSTOMER | apologetic:3 | normal | mid | normal
"Hi Karen, this is Naomi Bridges. I'm a little embarrassed but I had two overdraft fees hit my checking account last week — seventy dollars each, so a hundred forty total — and I was hoping to see what could be done about them. They came from a week when I was on vacation and miscalculated."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hi Ms. Bridges, no need to be embarrassed at all — this is a very common situation and you're calling exactly the right person. Let me see what we can do together."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling about overdraft fees from last week. I can certainly look into that. Before I look at the account, I'll need to verify a few details. Could you give me your account number?"
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Five-five-zero-three, one-one-four-eight, seven-two."
```

```
[T07] AGENT | professional:3 | normal | mid | normal | (typing)
"Date of birth?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"August twenty-third, nineteen-ninety-two."
```

```
[T09] AGENT | professional:3 | normal | mid | normal
"Last four of your Social?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Three-three-zero-eight."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"And the full legal name on the account?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Naomi Eve Bridges."
```

```
[T13] AGENT | reassuring:3 | normal | mid | normal
"You're fully verified, Ms. Bridges."
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"Thank you."
```

```
[T15] AGENT | empathetic:3 | normal | mid | normal
"So tell me about what happened during the vacation week — that way I'll have the right context when I look at the fees on the system."
```

```
[T16] CUSTOMER | apologetic:3 | normal | mid | normal
"I was on a cruise out of Miami. I had what I thought was an accurate balance, and I used my debit card for a couple of charges on shore — eighty dollars at one restaurant and about a hundred at a shop. Both of those overdrafted my account by a small amount each, and the fees were seventy dollars per item. The annoying part is I deposited two days later when I got home and the overdraft itself only existed for about thirty-six hours."
```

```
[T17] AGENT | empathetic:3 | normal | mid | normal
"That's an extremely common pattern — vacation spending, miscount, paycheck or transfer hits a couple of days later, and the fees stick even though the account is fine within the same week. I want to acknowledge how frustrating that is, especially for what was probably less than a hundred dollars actually overdrafted."
```

```
[T18] CUSTOMER | partially_satisfied:3 | normal | mid | normal
"Yeah. That's exactly it."
```

```
[T19] AGENT | professional:3 | normal | mid | normal | (typing)
"Let me pull up your account and look at the fees and the context."
```

```
[T20] CUSTOMER | calm:2 | normal | mid | normal
"Sure."
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Okay, I can see both fees clearly. October eleventh — overdraft on the eighty-dollar restaurant charge, seventy-dollar fee. October eleventh again — overdraft on the one-hundred-dollar retail charge, seventy-dollar fee. Total one forty in fees. October thirteenth — a deposit of twenty-two hundred dollars brought the account positive again. Net overdraft duration about thirty-six hours, just as you described."
```

```
[T22] CUSTOMER | cooperative:3 | normal | mid | normal
"That's right."
```

```
[T23] AGENT | warm:3 | normal | mid | normal
"So here's the picture from my side. The fees are valid in the sense that the transactions did overdraft the account. But the bigger context — short-duration overdraft, customer covered it within days, no prior overdraft pattern — is exactly the kind of case our courtesy waiver policy is designed for."
```

```
[T24] CUSTOMER | hopeful:3 | normal | mid | normal
"Okay."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"Let me do two quick checks before I apply anything."
```

```
[T26] CUSTOMER | cooperative:3 | normal | mid | normal
"Sure."
```

```
[T27] AGENT | professional:3 | normal | mid | normal | (typing)
"Check one — our courtesy waiver policy allows one waiver per account per one hundred and eighty days. I'm looking at your account history — no courtesy waivers in the last six months. So you qualify cleanly for a waiver today."
```

```
[T28] CUSTOMER | hopeful:3 | normal | mid | normal
"Good."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Check two — we look at whether there's a pattern of repeat fee complaints in the last ninety days that would route the decision differently. Your account is clean on that front. No pattern."
```

```
[T30] CUSTOMER | cooperative:3 | normal | mid | normal
"Right."
```

```
[T31] AGENT | reassuring:3 | normal | mid | normal
"And the total amount — one hundred forty dollars — is well within my single-call authorization cap of two hundred fifty dollars. So I can apply the full reversal directly on this call. No ticket needed."
```

```
[T32] CUSTOMER | grateful:3 | normal | mid | normal
"Oh — that's wonderful."
```

```
[T33] AGENT | professional:3 | normal | mid | normal | (typing)
"Applying the fee waiver now. Both seventy-dollar fees credited back under courtesy code A-D-J dash fee dash waive."
```

```
[T34] AGENT | warm:3 | normal | mid | normal
"Done. One hundred forty dollars is back in your account effective immediately, and it will be visible as available balance now and on your next statement as two credit line items."
```

```
[T35] CUSTOMER | grateful:4 | normal | mid | normal
"Karen, that's such a relief. Thank you."
```

```
[T36] AGENT | warm:3 | normal | mid | normal
"You're very welcome. While we're on the line, I'd like to set you up so that next time you're on vacation and miscount, this doesn't happen again. Would you be open to that?"
```

```
[T37] CUSTOMER | curious:3 | normal | mid | normal
"Yes, please."
```

```
[T38] AGENT | professional:3 | normal | mid | normal
"Two options. Option one — overdraft transfer protection from your savings, which I see you have. If a charge would overdraft your checking, the system pulls the difference from savings automatically. There's a twelve-dollar transfer fee per occurrence, which is much less than the seventy-dollar overdraft fee. Option two — overdraft transfer from a backup checking account if you have one elsewhere, same mechanism. Or you can have both as backups."
```

```
[T39] CUSTOMER | thoughtful:3 | normal | mid | normal
"Just the savings link is plenty. I don't have backup checking elsewhere."
```

```
[T40] AGENT | professional:3 | normal | mid | normal | (typing)
"Linking your savings ending six-six-zero-one as the overdraft transfer source. Active immediately. Twelve-dollar transfer fee if it ever has to pull."
```

```
[T41] CUSTOMER | satisfied:3 | normal | mid | normal
"Wonderful."
```

```
[T42] AGENT | warm:3 | normal | mid | normal
"And just to give you the picture — what happened on the vacation week is exactly the kind of innocent timing miss the courtesy policy is designed for. You've now got the safety net of overdraft transfer protection in place, so even if there's another timing issue, the worst case is a twelve-dollar transfer rather than a seventy-dollar overdraft fee."
```

```
[T43] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you reported two overdraft fees from October eleventh totaling one hundred forty dollars during a vacation. I confirmed your eligibility under the courtesy policy — no prior waivers in the last six months, no repeat-complaint flag, amount within my authority. Applied the full one hundred forty dollar reversal today. Linked your savings account ending six-six-zero-one for overdraft transfer protection going forward. Does that all sound right, Ms. Bridges?"
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T45] CUSTOMER | grateful:3 | normal | mid | normal
"No, that more than covers it. Karen, you turned a really stressful situation into a non-issue. Thank you."
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is M-T-B dash three-four-zero-zero-five-five-eight. You'll receive a brief survey after we hang up — your feedback is appreciated. Take care, Ms. Bridges."
```
