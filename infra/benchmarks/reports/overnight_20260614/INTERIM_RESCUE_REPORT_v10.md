# Interim Rescue Report v10

Run was stopped by user request.

Used existing checkpoint outputs to apply interpretation-first merge for `emotion_shift`:
- merged `dismissive_tone` + `missing_acknowledgment` into `tone_rudeness`
- kept `interruption` and `none`

This reduces label ambiguity while preserving FR-5 intent (agent behavior cause).

Interim checkpoint coverage:
- `emotion_shift`: 66/170 samples completed
- `nli_policy`: 0/172 samples completed

Interim ranking should be treated as directional until full-run completion.
