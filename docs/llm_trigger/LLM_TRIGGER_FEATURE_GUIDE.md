# LLM Trigger Feature Guide

## Purpose

The LLM Trigger feature evaluates customer-agent interactions and returns coaching/compliance signals through a three-component pipeline:

1. **RAG Retrieval Layer** — resolves SOP, policy, and knowledge base grounding context from Qdrant vector collections
2. **Policy Compliance Evaluator** — transcript-level compliance judge that produces a structured compliance report
3. **NLI Policy Check** — single-claim policy alignment check that validates agent statements against policy context

These components feed three analysis dimensions:

1. Emotion Shift: text vs acoustic mismatch and dissonance analysis
2. Process Adherence: SOP step coverage and resolution quality (uses SOP retrieval)
3. NLI Policy: contradiction/entailment check against policy context (uses Policy retrieval)

This guide documents architecture, data flow, folder structure, runtime behavior, and testing so the team can maintain and extend the feature safely.

## Evidence-Anchored Explainability

The trigger pipeline now emits a shared explainability layer instead of returning only session-level verdicts.

Manager-facing output is split into:

1. Span-Level Trigger Attribution
- Anchors emotion, SOP, and policy triggers to a specific utterance span.
- Adds `evidenceSpan`, `policyReference`, `reasoning`, and `evidenceChain`.
- Uses the same payload family for both emotion-trigger and RAG-driven findings.

2. Retrieval Provenance Scoring
- Anchors factual or compliance claims to the retrieved policy/SOP chunk used for review.
- Adds `claimSpan`, `retrievedPolicy`, `semanticSimilarity`, `nliVerdict`, and `provenance`.

See `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md` for the full shared contract.

## High-Level Architecture

1. Backend interaction detail endpoint can request LLM trigger evaluation.
2. The three-component pipeline executes:
   a. **RAG retrieval** resolves SOP/policy/KB grounding context from Qdrant.
   b. **Policy Compliance Evaluator** assesses transcript-level compliance and produces a structured report.
   c. **NLI Policy Check** validates individual agent claims against policy context.
3. SOP context is resolved with priority order:
   - Manual SOP standards (organization-specific parsed markdown)
   - Qdrant retrieval fallback (`vocalmind_sop_parents`, doc_type="sop")
4. Policy context is resolved via:
   - Active organization policies from database
   - Qdrant retrieval fallback (`vocalmind_parents`, doc_type="policy")
5. KB context is available on-demand via `KBRetriever` for claim validation lookups.
6. Results are mapped into a frontend-friendly payload.
7. Manager and Agent views render diagnostics and coaching insights.
8. Manager detail view renders evidence cards that connect claim -> evidence -> verdict.

## Core Backend Files

1. `backend/app/api/routes/interactions.py`
- Exposes interaction detail endpoint with optional LLM trigger fields.
- Maps internal report to API payload with `_map_llm_trigger_report`.
- Resolves organization slug via `_resolve_llm_org_filter`.

2. `backend/app/llm_trigger/service.py`
- Main orchestration and heuristics.
- Runs chains for emotion/process/NLI.
- Contains rolling window helpers, evidence construction, deterministic guards.

3. `backend/app/llm_trigger/retrieval.py`
- SOP retrieval resolver.
- Manual SOP path takes precedence.
- Falls back to Qdrant retrieval.

4. `backend/app/llm_trigger/chains.py`
- LangChain chain builders for the three analysis tasks.

5. `backend/app/llm_trigger/prompts.py`
- Prompt templates and output constraints.

6. `backend/app/llm_trigger/schemas.py`
- Typed response contracts for internal LLM trigger objects.

## Frontend Files

1. `frontend/src/app/services/api.ts`
- Type definitions for `llmTriggers` payload.
- Interaction detail request supports LLM options.

2. `frontend/src/app/components/manager/SessionDetail.tsx`
- Renders manager-focused trigger diagnostics.
- Supports LLM refresh action.
- Hosts the Evidence-Anchored Explainability panel.

3. `frontend/src/app/components/manager/EvidenceAnchoredExplainabilityPanel.tsx`
- Renders trigger attribution cards and claim provenance cards.
- Supports timestamp jump-to-audio interactions.

4. `frontend/src/app/components/agent/AgentCallDetail.tsx`
- Renders coaching-focused trigger insights.
- Supports LLM refresh action.

## SOP and Policy Folder Structure

Canonical root:

`storage/docs/`

Per organization:

1. `storage/docs/{org}/policy-docs/*.pdf`
- Source policy PDFs.
- Consumed by RAG ingestion (Docling converts PDF -> markdown).

2. `storage/docs/{org}/sop-procedures/*.pdf`
- Source SOP PDFs from organizations.
- Also ingested and converted by Docling.

3. `storage/docs/{org}/knowledge-base/*.pdf`
- Knowledge base reference documents.
- Indexed as `kb` doc type for claim validation lookups.

## Parsed Markdown and Runtime Consumption

1. RAG ingestion writes converted markdown into:
- `storage/docs/{org}/parsed-docs/*.md`

2. Backend SOP retrieval reads SOP context from parsed markdown:
- For each SOP PDF in `sop-procedures`, backend looks up matching stem in `parsed_docs`.
- Example:
  - source: `storage/docs/nexalink/sop-procedures/SOP_01_refund_request_processing.pdf`
  - parsed: `storage/docs/nexalink/parsed-docs/sops/SOP_01_refund_request_processing.md`

3. If no parsed markdown exists, retrieval has backward compatibility fallback for direct text files in `sop-procedures` (`.md` / `.txt`).

## Config Keys

### Backend (`backend/app/core/config.py`)

1. `SOP_DOCS_ROOT`
- Default: `storage/docs`

2. `SOP_PARSED_DOCS_ROOT`
- Default: `storage/docs` (resolved as `storage/docs/{org}/parsed-docs`)

3. `POLICY_DOCS_ROOT` / `KNOWLEDGE_DOCS_ROOT`
- Default: `storage/docs` (all three doc types share one root; type is determined by subfolder name)

4. `SOP_RETRIEVAL_TOP_K`
- Used for Qdrant fallback retrieval.

5. `QDRANT_COLLECTION_SOP_PARENTS` and `QDRANT_COLLECTION_SOP_CHILDREN`
- Stores specialized SOP vectors separately from Policies to eliminate RAG cross-pollution.

### RAG (`services/rag/config.py`, `.env`)

1. `DOCS_DIR`
- Expected to point to `storage/docs`

2. `PARSED_DIR`
- Base output root for parsed markdown and pipeline report.

## Endpoint Behavior

Interaction detail supports these query options:

1. `include_llm_triggers=true`
- Request LLM trigger payload.

2. `llm_org_filter=<org>`
- Optional explicit org override.

3. `llm_force_rerun=true`
- Recompute (used by refresh controls).

If `llm_org_filter` is omitted, backend resolves org slug from interaction -> organization relation.

## Explainability Payload Surface

The interaction detail response now exposes:

1. `utterances[].sequenceIndex`
- Stable utterance index used by evidence cards.

2. `emotionTriggers.explainability.triggerAttributions`
- Emotion-side span attributions.

3. `ragCompliance.explainability.triggerAttributions`
- SOP and policy trigger attributions derived from compliance review.

4. `ragCompliance.explainability.claimProvenance`
- Claim-level retrieval provenance for policy-grounded verdicts.

5. `llmTriggers.explainability`
- Combined manager-friendly aggregation of all trigger attributions plus claim provenance.

## Retrieval Priority

### SOP Context (for process adherence analysis)

1. If supplied `retrieved_sop_from_pinecone` is non-empty, use it.
2. Else attempt manual SOP context from `storage/docs/{org}/sop-procedures` via parsed markdown.
3. Else query dedicated SOP Qdrant fallback (`SOPRetriever` pointing to `vocalmind_sop_parents`, doc_type="sop").

### Policy Context (for NLI policy check)

1. If `ground_truth_policy` is supplied, use it.
2. Else load active organization policies from the database.
3. Else query `PolicyRetriever` (`vocalmind_parents`, doc_type="policy").

### Knowledge Base Context (for claim validation)

1. `KBRetriever` queries `vocalmind_sop_parents` with doc_type="kb".
2. Available on-demand for verifying agent factual claims against reference material.

## Ingestion Behavior for PDF Discovery

RAG ingestion scans per org for three document type folders:

1. `policy-docs` → indexed as doc_type="policy" into `vocalmind_parents` / `vocalmind_children`
2. `sop-procedures` → indexed as doc_type="sop" into `vocalmind_sop_parents` / `vocalmind_sop_children`
3. `knowledge-base` → indexed as doc_type="kb" into `vocalmind_sop_parents` / `vocalmind_sop_children`

Legacy fallback remains for org root PDFs.

## Full Validation Command

Use Make target from repository root:

`make llm-trigger-test`

This runs:

1. Backend LLM-trigger tests:
- `tests/test_llm_trigger_service.py`
- `tests/test_interactions_llm_triggers.py`
- `tests/test_sop_retrieval.py`

2. RAG ingestion tests:
- `services/rag/tests/test_ingest.py`

3. Frontend LLM section test:
- `frontend/src/tests/LLMTriggerSections.test.tsx`

## Test Coverage Summary

### Backend

1. `test_llm_trigger_service.py`
- Emotion shift heuristics and chain path
- Process adherence evaluation merge behavior
- Rolling windows and citations

2. `test_interactions_llm_triggers.py`
- API payload mapper shape and field mapping
- Includes explainability mapping assertions

3. `test_sop_retrieval.py`
- PDF-first SOP retrieval from parsed docs
- Fallback to direct text SOP files
- Priority over Qdrant when manual SOP exists

### RAG

1. `services/rag/tests/test_ingest.py`
- Discovery of PDFs in policy-docs and sop-procedures
- Existing cleaning/chunking/metadata validation

### Frontend

1. `LLMTriggerSections.test.tsx`
- Manager and Agent views render trigger sections correctly

2. `SessionDetail.test.tsx`
- Manager detail page renders evidence-anchored explainability cards and provenance details

## Operational Runbook

When adding or updating organization docs:

1. Place policy PDFs in `policy-docs`.
2. Place SOP PDFs in `sop-procedures`.
3. Run ingestion to regenerate parsed markdown and vectors.
4. Run `make llm-trigger-test`.
5. Validate in UI interaction detail pages with refresh action.

## Troubleshooting

1. LLM triggers unavailable
- Check backend logs around `evaluate_interaction_triggers`.
- Confirm `include_llm_triggers=true` is passed.

2. SOP steps missing unexpectedly
- Ensure SOP PDFs exist in `sop-procedures`.
- Ensure parsed markdown exists in `storage/docs/{org}/parsed-docs` after ingestion.
- Ensure file stems match expected names.

3. No policy context
- Verify `DOCS_DIR` points to `storage/docs`.
- Re-run ingestion and confirm Qdrant collections are populated.

4. Wrong organization SOP used
- Validate interaction organization mapping.
- Optionally pass explicit `llm_org_filter` to debug.

## Extension Notes

If adding new analysis dimensions:

1. Add schema in `schemas.py`.
2. Add prompt + chain builder.
3. Integrate into `evaluate_interaction_triggers`.
4. Map new fields in interactions route payload mapper.
5. Extend frontend types and views.
6. Add backend + frontend tests and include in `llm-trigger-test` target.
