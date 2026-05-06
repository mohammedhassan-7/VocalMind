# RAG Overview

## Purpose

The RAG service is the **retrieval layer** of VocalMind's three-component pipeline:

1. **RAG (this service)** — retrieval-only: parses, indexes, and retrieves document chunks
2. **Policy Compliance Evaluator** — transcript-level compliance judge/report generator (in `backend/app/llm_trigger/service.py`)
3. **NLI Policy Check** — single-claim policy alignment check used inside the LLM Trigger pipeline

The RAG service itself combines:
1. Docling PDF parsing
2. Local embeddings (Ollama)
3. Qdrant vector search (dual collections)
4. Groq LLM synthesis for standalone query mode

It also feeds the Evidence-Anchored Explainability Layer used in manager call review.

## Key Concepts

1. Three document types
- **Policy** (`policy-docs/`): compliance rules and standards
- **SOP** (`sop-procedures/`): step-by-step operational procedures
- **Knowledge Base** (`knowledge-base/`): factual reference material for claim validation

2. Mixed-granularity indexing
- Policy documents: both parent (full sections) and child (compact snippets) collections
- SOP and KB documents: parent collection only (header-level sections, no child splitting)

> **Design rationale.** Parents are large H1/H2/H3 sections — the whole rule, fee
> table, or escalation step. Children are 400-char recursive splits with 80-char
> overlap — narrow, semantically targeted spans. Granularity is chosen by the
> *consumer's* need, not by document type:
>
> | Consumer | Needs | Collection used |
> |---|---|---|
> | Policy compliance evaluator (transcript-level) | The full rule with all conditions, exceptions, and obligations | **policy parents** (`QDRANT_COLLECTION_PARENTS`) |
> | NLI policy check (single claim → policy) | A focused policy clause, self-contained, to NLI against | **policy parents** |
> | Process adherence (SOP) | Full procedure step block | **SOP parents** (`QDRANT_COLLECTION_SOP_PARENTS`) |
> | KB lookup (claim validation) | Reference fact passage | **SOP parents** (KB shares the parents-only collection) |
> | Manager-assistant Q&A / answer synthesis | Precise span to quote in the answer | **policy children** (`collection_children`) |
>
> Only policy documents need dual granularity: judge with the wide section, answer
> with the narrow span. SOP and KB are never used for free-form Q&A — they're
> always retrieved as a whole procedure or fact card — so we skip the child split
> for them entirely.

3. Per-organization isolation
- Documents are discovered by org folder under `storage/docs/{org}`
- Retrieval can be filtered by org metadata

4. Query modes
- Compliance / NLI / SOP / KB → **parent** collections (broader context the judge needs to reason against the whole rule).
- Answer synthesis (manager-assistant) → **policy children** (precise span to quote back to the user).

5. Retrieval provenance
- Retrieved chunks can be surfaced with similarity, reference path, and lightweight verdict metadata.
- Interaction detail pages expose this through `claimProvenance`.
- The standalone RAG route exposes `retrieval_provenance`.

## Main Runtime Components

1. `services/rag/query_engine.py`
- Embeds query text via Ollama (with `/api/embed` and `/api/embeddings` fallback)
- Queries Qdrant with optional org filter
- Synthesizes final response using Groq via LlamaIndex
- Logs query traces in `services/rag/logs`

2. `services/rag/evaluator.py`
- Structured scoring helpers for compliance and answer quality

3. `services/rag/config.py`
- Central settings for model, endpoints, collections, and paths

4. `backend/app/api/routes/rag.py`
- Wraps RAG results for the frontend API.
- Returns `retrieval_provenance` on `/api/v1/rag/query`.

## Collections

1. Policy Parents
- Name: `vocalmind_parents` (default, config: `QDRANT_COLLECTION_PARENTS`)
- Content: larger policy sections (H1/H2/H3 header splits)
- Usage: policy-level interpretation and consistency checks

2. Policy Children
- Name: `vocalmind_children` (default, config: `collection_children`)
- Content: shorter precision snippets (recursive 400-char splits)
- Usage: pinpoint factual grounding for answer checks

3. SOP + KB Parents
- Name: `vocalmind_sop_parents` (default, config: `QDRANT_COLLECTION_SOP_PARENTS` / `collection_sop_parents`)
- Content: SOP procedure sections and Knowledge Base reference chunks (header-level splits only, no child collection)
- Usage: process-adherence checks (doc_type="sop") and claim validation lookups (doc_type="kb")

> **Note:** SOP and KB documents are NOT split into a separate children collection. Only policy documents have both parent and child granularity.

## Directory Layout (Current)

1. Source docs
- `storage/docs/{org}/policy-docs/*.pdf`
- `storage/docs/{org}/sop-procedures/*.pdf`
- `storage/docs/{org}/knowledge-base/*.pdf`

2. Parsed markdown outputs
- `storage/docs/{org}/parsed-docs/policies/*.md` (policy docs)
- `storage/docs/{org}/parsed-docs/sops/*.md` (SOP docs)
- `storage/docs/{org}/parsed-docs/kb/*.md` (knowledge base docs)

3. Pipeline report
- `storage/docs/_pipeline_report.json`

## Config Summary

1. `DOCS_DIR`
- Base source root (default: `storage/docs`)

2. `PARSED_DIR`
- Base output root for parsed markdown + pipeline report (default: `storage/docs`)

3. `QDRANT_URL`
- Vector DB endpoint

4. `OLLAMA_BASE_URL` / `EMBEDDING_MODEL`
- Embedding provider settings

5. `GROQ_API_KEY`
- LLM synthesis provider

## Typical Flow

1. Ingestion parses PDFs and indexes vectors (policies → `vocalmind_parents`, SOPs/KB → `vocalmind_sop_parents`)
2. Query engine retrieves relevant chunks
3. Groq synthesizes response from retrieved context
4. Retrieval provenance is attached for explainability and auditability
5. Logs and timing are stored for auditability

## Relationship to LLM Trigger Pipeline

The LLM trigger pipeline consumes RAG retrieval through dedicated retrievers:

1. `SOPRetriever` — queries `vocalmind_sop_parents` with doc_type="sop" for process-adherence analysis
2. `PolicyRetriever` — queries `vocalmind_parents` with doc_type="policy" for NLI policy checks
3. `KBRetriever` — queries `vocalmind_sop_parents` with doc_type="kb" for claim validation lookups

The RAG service itself does not perform compliance evaluation — it provides the retrieval substrate that the Policy Compliance Evaluator and NLI Policy Check consume.

## Testing

Primary tests:
1. `services/rag/tests/test_ingest.py`
2. `services/rag/tests/test_query_engine.py`
3. `services/rag/tests/test_evaluator.py`
4. `services/rag/tests/test_config.py`
5. `backend/tests/test_interactions_llm_triggers.py`
6. `backend/tests/test_sop_retrieval.py`

Run:

```bash
cd services/rag
uv run pytest tests/ -v
```
