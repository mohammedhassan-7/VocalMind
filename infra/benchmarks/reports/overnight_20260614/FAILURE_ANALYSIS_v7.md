# Stage failure analysis

## emotion_shift — `kimi-k2.5:cloud` (n=170)

- **Exact:** 90/170 (52.9%)
- **Partial:** 0
- **No match:** 80
- **Unparseable:** 0

| GT | Predicted | Count | Example IDs |
|---|---|---:|---|
| passive_aggression | none | 37 | es_003, es_005, es_009 |
| cross_modal | passive_aggression | 13 | es_014, es_018, es_026 |
| cross_modal | sarcasm | 9 | es_010, es_034, es_050 |
| cross_modal | none | 8 | es_006, es_030, es_062 |
| passive_aggression | sarcasm | 3 | es_013, es_017, es_041 |
| none | passive_aggression | 3 | es_027, es_035, es_099 |
| sarcasm | none | 3 | es_052, es_n041, es_n045 |
| none | sarcasm | 3 | es_059, es_116, es_n038 |
| sarcasm | passive_aggression | 1 | es_020 |

## nli_policy — `ministral-3:8b` (n=172)

- **Exact:** 89/172 (51.7%)
- **Partial:** 0
- **No match:** 83
- **Unparseable:** 0

| GT | Predicted | Count | Example IDs |
|---|---|---:|---|
| Policy Hallucination | Contradiction | 38 | nli_004, nli_011, nli_015 |
| Benign Deviation | Contradiction | 21 | nli_013, nli_021, nli_029 |
| Entailment | Benign Deviation | 5 | nli_020, nli_036, nli_044 |
| Benign Deviation | Entailment | 5 | nli_065, nli_069, nli_081 |
| Entailment | Contradiction | 4 | nli_006, nli_102, nli_103 |
| Contradiction | Entailment | 4 | nli_112, nli_116, nli_n011 |
| Policy Hallucination | Entailment | 2 | nli_120, nli_121 |
| Contradiction / Policy Hallucination | Contradiction | 1 | nli_005 |
| Policy Hallucination / Contradiction | Contradiction | 1 | nli_009 |
| Contradiction | Benign Deviation | 1 | nli_113 |
| Contradiction / Policy Hallucination | Entailment | 1 | nli_n017 |
