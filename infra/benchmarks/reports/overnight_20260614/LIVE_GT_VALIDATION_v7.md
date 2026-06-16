# Live production GT validation v7

**Generated:** 2026-06-15 14:05 UTC  
**Manifest:** `validation_manifest_v7.json` (15 evenly-spaced samples/stage)  
**Method:** production chains + `ground_truth_scorer` on fresh API responses.

## emotion_shift

- **Model:** `kimi-k2.5:cloud`
- **Live samples:** 15 (from population n=170)
- **Parse OK:** 15/15 (100%)
- **GT exact:** 4/15 (27%)

| sample_id | parse | GT match |
|---|---|---|
| es_001 | True | exact |
| es_012 | True | no_match |
| es_023 | True | exact |
| es_034 | True | no_match |
| es_045 | True | no_match |
| es_056 | True | no_match |
| es_067 | True | exact |
| es_078 | True | no_match |
| es_089 | True | no_match |
| es_100 | True | no_match |
| es_111 | True | no_match |
| es_n002 | True | no_match |
| es_n013 | True | no_match |
| es_n024 | True | no_match |
| es_n035 | True | exact |

## process_adherence

- **Model:** `kimi-k2.6:cloud`
- **Live samples:** 15 (from population n=153)
- **Parse OK:** 15/15 (100%)
- **GT exact:** 7/15 (47%)

| sample_id | parse | GT match |
|---|---|---|
| pa_001 | True | exact |
| pa_011 | True | exact |
| pa_021 | True | exact |
| pa_031 | True | no_match |
| pa_041 | True | no_match |
| pa_051 | True | exact |
| pa_061 | True | no_match |
| pa_071 | True | no_match |
| pa_081 | True | no_match |
| pa_091 | True | exact |
| pa_101 | True | exact |
| pa_n008 | True | no_match |
| pa_n018 | True | no_match |
| pa_n028 | True | exact |
| pa_n038 | True | no_match |

## nli_policy

- **Model:** `ministral-3:8b`
- **Live samples:** 15 (from population n=172)
- **Parse OK:** 15/15 (100%)
- **GT exact:** 7/15 (47%)

| sample_id | parse | GT match |
|---|---|---|
| nli_001 | True | exact |
| nli_012 | True | no_match |
| nli_023 | True | no_match |
| nli_034 | True | exact |
| nli_045 | True | no_match |
| nli_056 | True | exact |
| nli_067 | True | no_match |
| nli_078 | True | exact |
| nli_089 | True | no_match |
| nli_100 | True | exact |
| nli_111 | True | no_match |
| nli_122 | True | no_match |
| nli_n011 | True | exact |
| nli_n022 | True | no_match |
| nli_n033 | True | exact |
