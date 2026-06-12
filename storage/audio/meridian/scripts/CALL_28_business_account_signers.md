# CALL_28 — Update Business Account Authorized Signers

```yaml
call_id: CALL_28_business_account_signers
duration_estimate: 6m 45s
turns: 48
sop_primary: BNK-SOP-01 (KYC re-verification for new signer)
policy_refs: [BNK-CC-RULE-001, BNK-CC-RULE-002, BNK-CC-RULE-003, BNK-CC-RULE-004, BNK-CC-RULE-005, BNK-CC-RULE-006, BNK-SEC-RULE-001, BNK-SEC-RULE-002, BNK-REG-RULE-001, BNK-REG-RULE-002, BNK-CC-RULE-020, BNK-CC-RULE-021, BNK-CC-RULE-022, BNK-CC-RULE-023]
kb_refs: [Authorized Signer Change Procedure]
customer_profile:
  name: "Helena Voss"
  account_number: "M-T-B-BIZ 8821-4407-66"
  voice_hint: "female, late 30s, neutral US accent, controlled and methodical, an office manager who handles bank business for her family's commercial real estate firm"
agent_profile:
  name: "Andre"
  voice_hint: "male, mid-30s, neutral US accent, friendly methodical cadence"
emotional_arc: "professional -> engaged -> cooperative -> satisfied"
expected_outcome: "Customer is the control person on a commercial real estate LLC and wants to add her brother as an authorized signer (not a beneficial owner — he won't own equity). Andre verifies her as the control person, explains what the change requires (in-person ID verification for the new signer at a branch since he is not present on this call), opens an Authorized Signer Change ticket, schedules the brother's branch visit. PASS — clean SOP. No CIP/Beneficial Ownership trigger (no ownership change), but the new signer must still complete CIP at the branch."
```

## Coverage

| Element | Where | Notes |
|---|---|---|
| Greeting | T01 | BNK-CC-RULE-001 — PASS |
| Recording notice | T02 | BNK-CC-RULE-002, BNK-SEC-RULE-001 — PASS |
| Acknowledge reason for call | T05 | BNK-CC-RULE-003 — PASS |
| 3-of-5 verification (business, control-person) | T07–T13 | BNK-CC-RULE-004 — PASS |
| Beneficial ownership / control-person status verified | T15 | BNK-REG-RULE-002 — PASS |
| Third-party (new signer) NOT made changes for over the phone | T21 | BNK-CC-RULE-006 — PASS |
| Privacy data-use statement | T23 | BNK-SEC-RULE-002 — PASS |
| CIP for new signer scheduled (branch in-person) | T29 | BNK-REG-RULE-001 — PASS |
| Ownership-change distinction explained (NOT a Beneficial Owner) | T33 | BNK-REG-RULE-002 — PASS |
| Authorized Signer Change ticket opened | T37 | BNK-CC-RULE-015 — PASS |
| Branch visit appointment scheduled | T41 | Procedural — PASS |
| Root cause + resolution summary | T44–T45 | BNK-CC-RULE-020, BNK-CC-RULE-021 — PASS |
| Anything else + case ref + survey | T46, T48 | BNK-CC-RULE-022, BNK-CC-RULE-023 — PASS |

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
[T03] CUSTOMER | professional:3 | normal | mid | normal
"Hi Andre, this is Helena Voss with Voss Commercial Holdings LLC. I'd like to add my brother as an authorized signer on our business account."
```

```
[T04] AGENT | warm:3 | normal | mid | normal
"Hello, Ms. Voss. Happy to help walk through that with you."
```

```
[T05] AGENT | professional:3 | normal | mid | normal
"I understand you are calling regarding adding an authorized signer to your business account, and I can certainly help. Because this is a business-account change, I'll need to verify you as the control person on file first."
```

```
[T06] CUSTOMER | cooperative:3 | normal | mid | normal
"Of course."
```

```
[T07] AGENT | professional:3 | normal | mid | normal
"Could you give me the business account number?"
```

```
[T08] CUSTOMER | cooperative:3 | normal | mid | normal
"Eight-eight-two-one, four-four-zero-seven, six-six."
```

```
[T09] AGENT | professional:3 | normal | mid | normal | (typing)
"And the full legal business name as registered with the state?"
```

```
[T10] CUSTOMER | cooperative:3 | normal | mid | normal
"Voss Commercial Holdings LLC, organized in Illinois."
```

```
[T11] AGENT | professional:3 | normal | mid | normal
"Your full legal name as it appears on the formation documents?"
```

```
[T12] CUSTOMER | cooperative:3 | normal | mid | normal
"Helena Marie Voss."
```

```
[T13] AGENT | professional:3 | normal | mid | normal
"Date of birth?"
```

```
[T14] CUSTOMER | cooperative:3 | normal | mid | normal
"October eleventh, nineteen-eighty-seven."
```

```
[T15] AGENT | reassuring:3 | normal | mid | normal
"All matches. I have you verified as the control person on the account, and our records show you and your mother Diane Voss as the two beneficial owners, fifty-fifty. Is that still accurate?"
```

```
[T16] CUSTOMER | cooperative:3 | normal | mid | normal
"Yes. No change in ownership."
```

```
[T17] AGENT | warm:3 | normal | mid | normal
"Wonderful. Tell me about the change you want to make — adding your brother. Just to confirm a couple of things up front: he would be an authorized signer, meaning he can sign for the LLC and operate the account, but he is not becoming an owner — correct?"
```

```
[T18] CUSTOMER | cooperative:3 | normal | mid | normal
"Correct. He's not buying in. He just helps us with day-to-day operations and we want him to be able to deposit rent checks and pay vendors."
```

```
[T19] AGENT | professional:3 | normal | mid | normal
"Understood, and that's a very common arrangement. Because he's not becoming an owner, this is just an authorized signer change — not a beneficial ownership update — which keeps the process a bit lighter on the regulatory side."
```

```
[T20] CUSTOMER | curious:3 | normal | mid | normal
"What does the process look like?"
```

```
[T21] AGENT | professional:3 | normal | mid | normal
"Here's the part I have to be transparent about. Even though we're not changing ownership, your brother does still need to be screened and ID-verified by us as the new signer — that's our Customer Identification Program requirement. And because he isn't on the call right now and isn't currently listed as an authorized party, I can't make changes for him over the phone today. He'll need to come into a branch in person with a government-issued photo ID."
```

```
[T22] CUSTOMER | thoughtful:3 | normal | mid | normal
"That makes sense. I figured."
```

```
[T23] AGENT | professional:3 | normal | mid | normal
"And one brief standard statement — your information is used solely to provide and service your accounts, in accordance with our Privacy Notice and applicable law."
```

```
[T24] CUSTOMER | cooperative:2 | normal | mid | normal
"Understood."
```

```
[T25] AGENT | professional:3 | normal | mid | normal
"So here's what I propose. I'll start the Authorized Signer Change ticket on this call. I'll capture your authorization as the control person — that part I can do over the phone since you are verified — and the ticket will sit open pending your brother's in-branch ID verification."
```

```
[T26] CUSTOMER | cooperative:3 | normal | mid | normal
"Okay."
```

```
[T27] AGENT | professional:3 | normal | mid | normal
"What's your brother's full legal name?"
```

```
[T28] CUSTOMER | cooperative:3 | normal | mid | normal
"Martin Edward Voss."
```

```
[T29] AGENT | professional:3 | normal | mid | normal
"Thank you. When he visits the branch, he'll need to bring a current driver's license or passport — current government-issued photo ID. They'll capture his date of birth, address, SSN, and run our CIP screen including the OFAC check. Once that clears — which is typically same-day — the signer change is activated and he can transact on the account."
```

```
[T30] CUSTOMER | curious:3 | normal | mid | normal
"Does he need to bring anything specific from the company side, or is the photo ID enough?"
```

```
[T31] AGENT | professional:3 | normal | mid | normal
"Photo ID and his Social Security card if he has it handy. The system will already see that he's the authorized-signer add tied to your LLC, so the branch banker can pull up the existing ticket. He doesn't need to bring anything from the company."
```

```
[T32] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T33] AGENT | professional:3 | normal | mid | normal
"One more clarification on the ownership distinction — because Martin is not becoming a beneficial owner, the company's ownership filings with us don't change. You and your mother remain the two fifty-percent beneficial owners. If at any point he were to acquire even a small ownership interest — five percent, ten percent, anything — we'd need to refile beneficial ownership under the Corporate Transparency Act. For now, no refile needed."
```

```
[T34] CUSTOMER | cooperative:3 | normal | mid | normal
"He won't be acquiring ownership. That's been the discussion. He gets a salary, not equity."
```

```
[T35] AGENT | warm:3 | normal | mid | normal
"Then we're clean. Authorized signer only."
```

```
[T36] CUSTOMER | satisfied:3 | normal | mid | normal
"Good."
```

```
[T37] AGENT | professional:3 | normal | mid | normal | (typing)
"Opening the Authorized Signer Change ticket now."
```

```
[T38] AGENT | reassuring:3 | normal | mid | normal
"Ticket is open and references the addition of Martin Edward Voss as an authorized signer, with your authorization on file."
```

```
[T39] CUSTOMER | satisfied:3 | normal | mid | normal
"Wonderful."
```

```
[T40] AGENT | professional:3 | normal | mid | normal
"Where's the most convenient branch for Martin?"
```

```
[T41] CUSTOMER | cooperative:3 | normal | mid | normal
"He's near the Skokie branch. He's free Thursday morning."
```

```
[T42] AGENT | professional:3 | normal | mid | normal | (typing)
"Scheduling a Thursday morning appointment at the Skokie branch — they'll see he has an open Authorized Signer Change ticket when he checks in. Confirmation will email to the address on file for the company, and Martin should receive an appointment-confirmation email at the email you provide for him in a moment."
```

```
[T43] CUSTOMER | cooperative:3 | normal | mid | normal
"Martin's email is m-voss at voss-commercial dot com."
```

```
[T44] AGENT | warm:3 | normal | mid | normal
"Captured. Confirmation will go out immediately."
```

```
[T45] AGENT | reassuring:3 | normal | mid | normal
"To summarize: you called to add your brother Martin Voss as an authorized signer on the Voss Commercial Holdings business account. I opened the Authorized Signer Change ticket with your authorization as control person, scheduled a Thursday morning branch appointment at the Skokie location for Martin to complete CIP and ID verification in person. Once that clears — usually same-day — Martin will be active on the account. Ownership remains unchanged. Does that all sound right, Ms. Voss?"
```

```
[T46] AGENT | warm:3 | normal | mid | normal
"Is there anything else I can help you with today?"
```

```
[T47] CUSTOMER | grateful:3 | normal | mid | normal
"No, that's exactly what I was hoping to hear. Thank you, Andre."
```

```
[T48] AGENT | warm:3 | normal | mid | normal
"My pleasure. Your case reference number is M-T-B dash two-eight-four-four-zero-zero-three. You'll receive a brief survey after we hang up — appreciate the feedback if you have a moment. Thanks for banking with Meridian."
```
